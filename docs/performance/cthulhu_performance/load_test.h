// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <memory>

#include <H5Cpp.h>
#include <boost/filesystem.hpp>
#include <boost/interprocess/managed_shared_memory.hpp>

#include <cthulhu/Framework.h>

namespace labgraph {

namespace benchmarks {

constexpr char STREAM_ID[] = "CTHULHU_LOAD_TEST";
constexpr char CONTEXT_NAME[] = "CTHULHU_LOAD_TEST_CONTEXT";
constexpr char CONDITION_NAME[] = "CTHULHU_LOAD_TEST_SETUP_SIGNAL";
constexpr char MUTEX_NAME[] = "CTHULHU_LOAD_TEST_SETUP_MUTEX";
constexpr char SUBSCRIBER_CONTEXT_NAME[] = "LOAD_TEST_SUBSCRIBER";
constexpr char PUBLISHER_CONTEXT_NAME[] = "LOAD_TEST_PUBLISHER";
constexpr char LOAD_TEST_SHM_NAME[] = "LOAD_TEST";
constexpr char HDF5_SAMPLE_SUMMARY_DATASET_NAME[] = "sample_summary";
constexpr char HDF5_COUNT_DATASET_NAME[] = "count";
constexpr size_t HDF5_FILE_LOCK_ATTEMPTS = 5;
constexpr long HDF5_FILE_LOCK_WAIT_SECS = 1;
constexpr size_t SAMPLE_DATA_SIZE = 10;

struct LoadTestSample : public cthulhu::AutoStreamSample {
  using T = LoadTestSample;

  cthulhu::FieldsBegin<T> begin;
  cthulhu::SampleField<double, T> timestamp{"timestamp", this};
  cthulhu::SampleField<uint64_t, T> counter{"counter", this};
  cthulhu::SampleField<std::array<uint64_t, SAMPLE_DATA_SIZE>, T> data{"data", this};
  cthulhu::DynamicSampleField<std::vector<uint64_t>, T> dynamicData{"dynamicData", this};
  cthulhu::FieldsEnd<T> end;

  CTHULHU_AUTOSTREAM_SAMPLE(LoadTestSample);
};

// Summary of a received sample - keeps timing/throughput information for analysis but
// discards the actual data
struct SampleSummary {
  double sentTimestamp;
  double receivedTimestamp;
  uint64_t counter;
  uint64_t size;
  uint64_t dynamicSize;
};

// Count of how many samples were sent/received by sample size
struct Count {
  bool sent;
  double duration;
  uint64_t count;
  uint64_t size;
  uint64_t dynamicSize;
};

using Clock = std::chrono::high_resolution_clock;

// Returns a HDF5 composite type for storing SampleSUmmary
H5::CompType getH5SampleSummaryType() {
  H5::CompType datasetType(sizeof(SampleSummary));
  datasetType.insertMember(
      H5std_string("sent_timestamp"),
      HOFFSET(SampleSummary, sentTimestamp),
      H5::PredType::NATIVE_DOUBLE);
  datasetType.insertMember(
      H5std_string("received_timestamp"),
      HOFFSET(SampleSummary, receivedTimestamp),
      H5::PredType::NATIVE_DOUBLE);
  datasetType.insertMember(
      H5std_string("counter"), HOFFSET(SampleSummary, counter), H5::PredType::NATIVE_UINT64);

  return datasetType;
}

// Returns a HDF5 composite type for storing Count
H5::CompType getH5CountType() {
  H5::CompType datasetType(sizeof(Count));
  datasetType.insertMember(H5std_string("sent"), HOFFSET(Count, sent), H5::PredType::NATIVE_HBOOL);
  datasetType.insertMember(
      H5std_string("duration"), HOFFSET(Count, duration), H5::PredType::NATIVE_DOUBLE);
  datasetType.insertMember(
      H5std_string("count"), HOFFSET(Count, count), H5::PredType::NATIVE_UINT64);
  datasetType.insertMember(H5std_string("size"), HOFFSET(Count, size), H5::PredType::NATIVE_UINT64);
  datasetType.insertMember(
      H5std_string("dynamic_size"), HOFFSET(Count, dynamicSize), H5::PredType::NATIVE_UINT64);

  return datasetType;
}

// Creates the dataset with the given name and data type if it doesn't already exist
void createH5DatasetIfNotExists(H5::H5File* file, const char* name, H5::DataType dataType) {
  if (H5Lexists(file->getId(), name, H5P_DEFAULT) <= 0) {
    hsize_t dims[1];
    dims[0] = 0;
    hsize_t maxdims[1];
    maxdims[0] = H5S_UNLIMITED;
    H5::DataSpace space(1, dims, maxdims);

    H5::DSetCreatPropList props;
    hsize_t chunkdims[1];
    chunkdims[0] = 1;
    props.setChunk(1, chunkdims);

    file->createDataSet(name, dataType, space, props);
  }
}

// Returns the dataset name for sample summaries for a particular dynamic block size
std::string getH5SampleSummaryDatasetName(size_t dynamicSize) {
  return std::string(HDF5_SAMPLE_SUMMARY_DATASET_NAME) + "_" + std::to_string(dynamicSize);
}

// Returns an HDF5 file at the given path, initializing datasets for SampleSummary and
// Count objects if they do not exist. Retries opening the file if the file is locked by
// another process.
std::unique_ptr<H5::H5File> getH5File(const std::string& outputFilePath) {
  H5std_string h5FileName(outputFilePath.c_str());
  std::unique_ptr<H5::H5File> file;

  for (size_t attemptsLeft = HDF5_FILE_LOCK_ATTEMPTS; attemptsLeft > 0; attemptsLeft--) {
    try {
      file = std::make_unique<H5::H5File>(
          h5FileName, boost::filesystem::exists(h5FileName) ? H5F_ACC_RDWR : H5F_ACC_TRUNC);
      break;
    } catch (const H5::FileIException& ex) {
      std::this_thread::sleep_for(std::chrono::seconds(HDF5_FILE_LOCK_WAIT_SECS));
    }
  }

  assert(file);

  createH5DatasetIfNotExists(file.get(), HDF5_COUNT_DATASET_NAME, getH5CountType());

  return file;
}

// Appends a contiguous array of objects to the given dataset.
void appendToH5Dataset(H5::DataSet& dataset, H5::DataType dataType, void* data, size_t numRows) {
  hsize_t existingDatasetSize[1];
  dataset.getSpace().getSimpleExtentDims(existingDatasetSize, NULL);

  hsize_t newDatasetSize[1];
  newDatasetSize[0] = existingDatasetSize[0] + numRows;
  dataset.extend(newDatasetSize);

  hsize_t diffSize[1] = {numRows};

  H5::DataSpace memSpace(1, diffSize);
  auto fileSpace = dataset.getSpace();
  fileSpace.selectHyperslab(H5S_SELECT_SET, diffSize, existingDatasetSize);

  dataset.write(data, dataType, memSpace, fileSpace);
}

} // namespace benchmarks

} // namespace labgraph
