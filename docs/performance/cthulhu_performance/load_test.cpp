// Copyright 2004-present Facebook. All Rights Reserved.

#include "load_test.h"

#include <chrono>
#include <ctime>
#include <iomanip>

#include <CLI/CLI.hpp>
#include <boost/filesystem.hpp>
#include <boost/predef.h>
#include <boost/process.hpp>

#define DEFAULT_LOG_CHANNEL "LOAD_TEST"
#include <logging/Checks.h>
#include <logging/Log.h>

using namespace labgraph::benchmarks;

CTHULHU_REGISTER_BASIC_STREAM_TYPE(LoadTest, LoadTestSample);

std::string getOutputFilePath() {
  auto currentTime = std::time(nullptr);
  auto localTime = *std::localtime(&currentTime);

  std::ostringstream fileNameStream;
  fileNameStream << "load_test_cpp_";
#if BOOST_OS_WINDOWS
  fileNameStream << "win";
#elif BOOST_OS_MACOS
  fileNameStream << "mac";
#elif BOOST_OS_LINUX
  fileNameStream << "linux";
#else
  fileNameStream << "other";
#endif
  fileNameStream << "_" << std::put_time(&localTime, "%Y%m%d_%H%M%S") << ".h5";
  std::string fileName = fileNameStream.str();

  auto outputFilePath =
      boost::filesystem::temp_directory_path() / boost::filesystem::path(fileName);
  return outputFilePath.make_preferred().string();
}

/**
 * This program tries to produce and consume Cthulhu samples as fast as possible and
 * prints statistics about how fast the system was able to do so.
 */
int main(int argc, char** argv) {
  CLI::App app{"LabGraph C++ Load Test"};
  double duration;
  size_t dynamicSize;
  bool manyDynamicSizes;
  std::string cleanCommand;
  std::string subscriberCommand;
  std::string publisherCommand;

  std::string outputFilePath = getOutputFilePath();
  app.add_option("-d,--duration", duration, "Load test duration in seconds")->default_val(60.0);
  app.add_option("-y,--dynamic-size", dynamicSize, "Size of dynamic parameter block")
      ->default_val(8);
  app.add_flag(
      "-m,--many-dynamic-sizes",
      manyDynamicSizes,
      "Test many sizes for the dynamic parameter block");
  app.add_option("-s,--subscriber-command", subscriberCommand, "Command to run for the subscriber")
      ->required();
  app.add_option("-p,--publisher-command", publisherCommand, "Command to run for the publisher")
      ->required();
  app.add_option("-c,--clean-command", cleanCommand, "Command to run to clean up shared memory")
      ->required();
  app.add_option("-o,--output-file", outputFilePath, "File to write output HDF5");

  CLI11_PARSE(app, argc, argv);

  std::vector<size_t> dynamicSizes;
  if (manyDynamicSizes) {
    // Log scale from 2^3 to 2^23
    for (size_t genDynamicSize = 8; genDynamicSize <= 8388608; genDynamicSize <<= 1) {
      dynamicSizes.emplace_back(genDynamicSize);
    }
  } else {
    dynamicSizes.emplace_back(dynamicSize);
  }

  for (const auto& testDynamicSize : dynamicSizes) {
    XR_CHECK(
        testDynamicSize % sizeof(uint64_t) == 0,
        "Expected dynamic size {} to be divisible by {}",
        testDynamicSize,
        sizeof(uint64_t));

    boost::process::child cleanChild(cleanCommand, "--hard");
    while (cleanChild.running()) {
      std::this_thread::yield();
    }

    XR_LOGI("Writing load test output to: {}", outputFilePath);
    XR_LOGI("Dynamic parameter block size: {}", testDynamicSize);

    XR_LOGI("Starting load test subscriber...");
    boost::process::child subscriberChild(
        subscriberCommand,
        "--duration",
        std::to_string(duration),
        "--output-file",
        outputFilePath,
        "--dynamic-size",
        std::to_string(testDynamicSize));

    XR_LOGI("Starting load test publisher...");
    boost::process::child publisherChild(
        publisherCommand,
        "--duration",
        std::to_string(duration),
        "--output-file",
        outputFilePath,
        "--dynamic-size",
        std::to_string(testDynamicSize));

    while (subscriberChild.running() || publisherChild.running()) {
      std::this_thread::yield();
    }

    XR_LOGI("Test for dynamic parameter block size {} complete", testDynamicSize);
  }

  XR_LOGI("Load test complete.");
}
