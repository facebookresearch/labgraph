// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <chrono>
#include <mutex>
#include <optional>

namespace cthulhu {

// PerformanceSummary holds the summary statistics computed by PerformanceMonitor.
struct PerformanceSummary {
  std::optional<std::chrono::duration<double>> minRuntime;
  std::optional<std::chrono::duration<double>> meanRuntime;
  std::optional<std::chrono::duration<double>> maxRuntime;
  std::chrono::duration<double> totalRuntime;
  uint64_t numCalls = 0;
  uint64_t numSamplesDropped = 0;
};

// PerformanceMonitor provides a way to measure the timing of callbacks and update
// some rolling statistics on those timings.
struct PerformanceMonitor {
  using ClockType = std::chrono::high_resolution_clock;

  void startMeasurement();
  void endMeasurement();
  void sampleDropped();
  PerformanceSummary getSummary();

 private:
  std::optional<ClockType::time_point> startTime_;
  PerformanceSummary summary_;
  std::mutex summaryMutex_;
};

} // namespace cthulhu
