#include "load_test.h"

#include <CLI/CLI.hpp>
#include <H5Cpp.h>
#include <boost/filesystem.hpp>
#include <boost/process.hpp>
#include <boost/process/environment.hpp>

#define DEFAULT_LOG_CHANNEL "LOAD_TEST_PUBLISHER"
#include <logging/Checks.h>
#include <logging/Log.h>

#include <cthulhu/Context.h>
#include <cthulhu/StreamInterface.h>

using namespace labgraph::benchmarks;

CTHULHU_REGISTER_BASIC_STREAM_TYPE(LoadTest, LoadTestSample);

int main(int argc, char** argv) {
  // Read command line options
  CLI::App app{"Labgraph C++ Load Test Publisher"};
  double duration;
  size_t dynamicSize;
  std::string outputFilePath;
  app.add_option("-d,--duration", duration, "Load test duration in seconds")->required(true);
  app.add_option("-y,--dynamic-size", dynamicSize, "Size of dynamic parameter block")
      ->default_val(SAMPLE_DATA_SIZE);
  app.add_option("-o,--output-file", outputFilePath, "File to write output HDF5")->required(true);
  CLI11_PARSE(app, argc, argv);

  XR_CHECK(
      dynamicSize % sizeof(uint64_t) == 0,
      "Expected dynamic size {} to be divisible by {}",
      dynamicSize,
      sizeof(uint64_t));

  XR_LOGI("Load test publisher started. (PID: {})", boost::this_process::get_id());

  // Retrieve information about the sample type from the type registry
  auto typeInfo = cthulhu::Framework::instance().typeRegistry()->findTypeName("LoadTest");
  const size_t sampleSize = typeInfo->sampleParameterSize();

  // Set up stream
  cthulhu::StreamDescription streamDesc(
      std::string(STREAM_ID),
      cthulhu::Framework::instance().typeRegistry()->findTypeName("LoadTest")->typeID());
  cthulhu::StreamInterface* stream =
      cthulhu::Framework::instance().streamRegistry()->registerStream(streamDesc);

  // Set up publisher
  cthulhu::StreamProducer producer(stream, true);

  // Publish samples for the duration
  XR_LOGI("Publishing for {} s...", duration);
  uint64_t counter = 0;
  const auto startTime = Clock::now();
  std::chrono::duration<double> testDuration(duration);
  for (auto currentTime = Clock::now(); (currentTime - startTime) < testDuration;
       currentTime = Clock::now()) {
    LoadTestSample sample;

    // Set timestamp and counter
    sample.timestamp =
        std::chrono::duration<double, std::ratio<1>>(currentTime.time_since_epoch()).count();
    sample.counter = counter;

    // Populate the fixed parameter block
    for (size_t idx = 0; idx < SAMPLE_DATA_SIZE; idx++) {
      sample.data.ptr()[idx] = counter + idx;
    }

    // Populate the dynamic vector
    std::shared_ptr<uint8_t> dynamicData =
        cthulhu::Framework::instance().memoryPool()->getBufferFromPool("", dynamicSize);
    uint64_t* dynamicDataPtr = reinterpret_cast<uint64_t*>(dynamicData.get());
    for (size_t idx = 0; idx < dynamicSize / sizeof(uint64_t); idx++) {
      dynamicDataPtr[idx] = counter + idx;
    }
    sample.dynamicData.setPtr(dynamicData, dynamicSize);

    // Publish the sample
    producer.produceSample(sample.getSample());
    counter++;
  }

  XR_LOGI("Samples sent: {}", counter);

  // Add the sent count to the HDF5 file
  auto h5File = getH5File(outputFilePath);
  auto countDataset = h5File->openDataSet(HDF5_COUNT_DATASET_NAME);
  Count sentCount{true, duration, counter, sampleSize + dynamicSize, dynamicSize};
  appendToH5Dataset(countDataset, getH5CountType(), &sentCount, 1);

  XR_LOGI("Load test publisher terminating.");
}
