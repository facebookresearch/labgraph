#include <cthulhu/PerformanceMonitor.h>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Checks.h>

namespace cthulhu {

void PerformanceMonitor::startMeasurement() {
  XR_DEV_CHECK(!startTime_, "Cannot start two performance measurements");
  startTime_ = ClockType::now();
}

void PerformanceMonitor::endMeasurement() {
  XR_DEV_CHECK(startTime_, "Tried to end performance measurement when none was in progress");
  std::chrono::duration<double> runtime = ClockType::now() - startTime_.value();
  startTime_.reset();

  std::scoped_lock<std::mutex> summaryLock(summaryMutex_);

  summary_.numCalls++;

  if (summary_.numCalls == 1) {
    // First measurement
    summary_.minRuntime = summary_.meanRuntime = summary_.maxRuntime = summary_.totalRuntime;
  } else {
    summary_.minRuntime = runtime < summary_.minRuntime ? runtime : summary_.minRuntime;
    summary_.maxRuntime = runtime > summary_.maxRuntime ? runtime : summary_.maxRuntime;
    summary_.totalRuntime += runtime;
    summary_.meanRuntime = summary_.totalRuntime / (double)summary_.numCalls;
  }
}

void PerformanceMonitor::sampleDropped() {
  std::scoped_lock<std::mutex> summaryLock(summaryMutex_);
  summary_.numSamplesDropped++;
}

PerformanceSummary PerformanceMonitor::getSummary() {
  std::scoped_lock<std::mutex> summaryLock(summaryMutex_);
  // Copy summary_ so that continued writes to it will not affect the returned summary
  return PerformanceSummary(summary_);
}

}; // namespace cthulhu
