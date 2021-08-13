// Copyright 2004-present Facebook. All Rights Reserved.

#include "load_test.h"

#include <vector>

#include <CLI/CLI.hpp>
#include <H5Cpp.h>
#include <boost/process.hpp>

#define DEFAULT_LOG_CHANNEL "LOAD_TEST_SUBSCRIBER"
#include <cthulhu/StreamInterface.h>
#include <logging/Log.h>

using namespace labgraph::benchmarks;

CTHULHU_REGISTER_BASIC_STREAM_TYPE(LoadTest, LoadTestSample);

int main(int argc, char** argv) {
  // Read command line options
  CLI::App app{"Labgraph C++ Load Test Subscriber"};
  double duration;
  size_t dynamicSize;
  std::string outputFilePath;
  app.add_option("-d,--duration", duration, "Load test duration in seconds")->required(true);
  app.add_option("-y,--dynamic-size", dynamicSize, "Size of dynamic parameter block")
      ->default_val(SAMPLE_DATA_SIZE);
  app.add_option("-o,--output-file", outputFilePath, "File to write output HDF5")->required(true);
  CLI11_PARSE(app, argc, argv);

  XR_LOGI("Load test subscriber started. (PID: {})", boost::this_process::get_id());

  // Retrieve information about the sample type from the type registry
  auto typeInfo = cthulhu::Framework::instance().typeRegistry()->findTypeName("LoadTest");
  const size_t sampleSize = typeInfo->sampleParameterSize();
  const size_t numDynamicParameters = typeInfo->sampleNumberDynamicFields();

  // Define the subscriber callback
  std::vector<SampleSummary> receivedData;
  std::function<void(const cthulhu::StreamSample&)> callback =
      [sampleSize, numDynamicParameters, &receivedData](const cthulhu::StreamSample& rawSample) {
        double receivedTimestamp =
            std::chrono::duration<double, std::ratio<1>>(Clock::now().time_since_epoch()).count();

        // Convert the generic StreamSample into a LoadTestSample
        LoadTestSample sample;
        sample.setSample(rawSample);

        // Check the sample data for correctness
        for (size_t idx = 0; idx < SAMPLE_DATA_SIZE; idx++) {
          if (sample.data.ptr()[idx] != sample.counter + idx) {
            XR_LOGE_ONCE("Incorrect parameter data received");
          }
        }

        // Check the dynamic parameter data for correctness
        for (size_t idx = 0; idx < sample.dynamicData.size(); idx++) {
          if (sample.dynamicData.ptr()[idx] != sample.counter + idx) {
            XR_LOGE("Incorrect dynamic parameter data received");
          }
        }

        // Compute the size of the dynamic parameters
        size_t dynamicSize = 0;
        for (size_t dynIdx = 0; dynIdx < numDynamicParameters; dynIdx++) {
          cthulhu::RawDynamic<>* rawDynamic = rawSample.dynamicParameters.get() + dynIdx;
          dynamicSize += rawDynamic->size();
        }

        // Add a SampleSummary for the received sample
        receivedData.push_back(
            {sample.timestamp,
             receivedTimestamp,
             sample.counter,
             sampleSize + dynamicSize,
             dynamicSize});
      };
  std::function<bool(const cthulhu::StreamConfig&)> configCallback = nullptr;

  // Wait for the publisher to create the stream
  cthulhu::StreamInterface* stream =
      cthulhu::Framework::instance().streamRegistry()->getStream(std::string(STREAM_ID));
  while (!stream) {
    XR_LOGI_ONCE("Waiting for stream to be created...");
    std::this_thread::yield();
    stream = cthulhu::Framework::instance().streamRegistry()->getStream(std::string(STREAM_ID));
  }

  cthulhu::PerformanceSummary performanceSummary;
  {
    // Define the subscriber
    cthulhu::StreamConsumer sub(stream, callback, configCallback, true);

    XR_LOGI("Subscribed for {} s...", duration);

    // Sleep while the publisher publishes (the subscriber callback will run in a
    // background thread)
    std::this_thread::sleep_for(std::chrono::duration<double>(duration));

    performanceSummary = sub.getPerformanceSummary();
  }

  // Log useful summary statistics

  uint64_t numSamplesReceived = receivedData.size();
  XR_LOGI("Samples received: {}", numSamplesReceived);

  // Compute latency and drop rate in one pass
  double minTimestamp = 0.0;
  double maxTimestamp = 0.0;
  uint64_t maxCounter = 0;
  double totalLatency = 0.0;
  for (size_t i = 0; i < receivedData.size(); i++) {
    auto data = receivedData[i];
    if (minTimestamp == 0.0 || data.sentTimestamp < minTimestamp) {
      minTimestamp = data.sentTimestamp;
    }
    if (maxTimestamp == 0.0 || data.sentTimestamp > maxTimestamp) {
      maxTimestamp = data.sentTimestamp;
    }
    if (data.counter > maxCounter) {
      maxCounter = data.counter;
    }
    totalLatency += data.receivedTimestamp - data.sentTimestamp;
  }

  // Log statistics collected by PerformanceSummary
  XR_LOGI(
      "Callback time: min {} s, max {} s, mean {} s",
      performanceSummary.minRuntime.value().count(),
      performanceSummary.maxRuntime.value().count(),
      performanceSummary.meanRuntime.value().count());
  double sampleRate = (double)receivedData.size() / (maxTimestamp - minTimestamp);
  XR_LOGI("Sample rate: {} Hz", sampleRate);
  double meanLatency = totalLatency / (double)receivedData.size();
  XR_LOGI("Mean latency: {} s", meanLatency);

  // Compute data rate
  size_t bytesReceived = 0;
  for (size_t idx = 0; idx < receivedData.size(); idx++) {
    bytesReceived += receivedData[idx].size;
  }
  double dataRate = (double)bytesReceived / (maxTimestamp - minTimestamp);
  XR_LOGI("Data rate: {} B/s", dataRate);
  size_t droppedSamples = (maxCounter + 1) - receivedData.size();
  double dropRate = (double)droppedSamples / ((double)droppedSamples + (double)receivedData.size());
  XR_LOGI("Dropped samples: {} ({}%)", droppedSamples, dropRate * 100.0);

  // Write SampleSummary and Count data to HDF5 file
  auto h5File = getH5File(outputFilePath);
  std::string datasetName = getH5SampleSummaryDatasetName(dynamicSize);
  createH5DatasetIfNotExists(h5File.get(), datasetName.c_str(), getH5SampleSummaryType());
  auto sampleSummaryDataset = h5File->openDataSet(datasetName.c_str());
  appendToH5Dataset(
      sampleSummaryDataset, getH5SampleSummaryType(), receivedData.data(), numSamplesReceived);

  auto countDataset = h5File->openDataSet(HDF5_COUNT_DATASET_NAME);
  Count receivedCount{false, duration, numSamplesReceived, sampleSize + dynamicSize, dynamicSize};
  appendToH5Dataset(countDataset, getH5CountType(), &receivedCount, 1);

  XR_LOGI("Load test subscriber terminating.");
}
