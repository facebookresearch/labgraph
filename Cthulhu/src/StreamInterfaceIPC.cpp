#include "StreamInterfaceIPC.h"

#include <iostream>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

#include <cthulhu/Framework.h>

#include <signal.h>
#include <chrono>
namespace cthulhu {

double getCurrentTimeSec() {
  auto now = std::chrono::high_resolution_clock::now();
  auto timeSinceEpoch =
      std::chrono::duration<double, std::chrono::seconds::period>(now.time_since_epoch());
  return timeSinceEpoch.count();
}

StreamConsumerIPC::StreamConsumerIPC(
    StreamInterfaceIPC* si,
    const std::function<bool(const StreamConfigIPC& config)>& configCallback,
    const std::function<bool(const StreamSampleIPC& sampleData)>& sampleCallback,
    bool updateConfig)
    : streamInterface_(si),
      configCallback_(configCallback),
      sampleCallback_(sampleCallback),
      stopSignal_{false} {
  if (!streamInterface_) {
    auto str = "Received invalid stream interface in IPC listener";
    XR_LOGE("{}", str);
    throw std::runtime_error(str);
  }
  {
    ScopedLockIPC streamLock(streamInterface_->streamLock);
    streamInterface_->numSubscribers_++;
  }
  // If updateConfig is false, grab any existing config timestamp
  // so the config doesn't get sent out.
  if (!updateConfig) {
    ScopedLockIPC dataLock(streamInterface_->dataLock);
    if (streamInterface_->config.has_value()) {
      latestConfigTime_ = streamInterface_->config->timestamp;
    }
  }

  thread_ = std::thread([this] {
    while (!stopSignal_.load()) {
      update();

      // Wait for signal
      ScopedLockIPC lock(streamInterface_->dataLock);
      streamInterface_->dataUpdate.timed_wait(
          lock, boost::get_system_time() + boost::posix_time::milliseconds(1));
    }
  });
}

StreamConsumerIPC::~StreamConsumerIPC() {
  // Grab the stream lock before we try to shut down our thread. This guarantees
  // that we won't try to shut it down while an IPC producer is pushing data out
  ScopedLockIPC lock(streamInterface_->streamLock);

  stopSignal_.store(true);
  if (thread_.joinable()) {
    thread_.join();
  }

  streamInterface_->numSubscribers_--;
}

void StreamConsumerIPC::update() {
  Framework::validate();

  ScopedLockIPC lock(streamInterface_->dataLock);
  const auto& config = streamInterface_->config;
  const auto& sample = streamInterface_->sample;
  if (config.has_value() && config->timestamp > latestConfigTime_) {
    latestConfigTime_ = config->timestamp;
    streamInterface_->configConsumedCount++;
    if (configCallback_ && !configCallback_(config->data)) {
      return;
    }
  }
  if (sample.has_value() && sample->timestamp > latestSampleTime_) {
    streamInterface_->sampleConsumedCount++;
    if (sampleCallback_) {
      if (sampleCallback_(sample->data)) {
        latestSampleTime_ = sample->timestamp;
      }
    }
  }
}

StreamProducerIPC::StreamProducerIPC(StreamInterfaceIPC* si) : streamInterface_(si) {
  ScopedLockIPC lock(streamInterface_->streamLock);
  if (streamInterface_->advertised_) {
    return;
  }
  streamInterface_->advertised_ = true;
  valid_ = true;
}

StreamProducerIPC::~StreamProducerIPC() {
  if (valid_) {
    ScopedLockIPC lock(streamInterface_->streamLock);
    streamInterface_->advertised_ = false;
  }
}

void StreamProducerIPC::configure(const StreamConfigIPC& configIn) {
  if (valid_) {
    configureValid(configIn);
  }
}

void StreamProducerIPC::configureValid(const StreamConfigIPC& configIn) {
  // Grab the stream lock so no one can join-in on the stream mid-call
  // We want to have a fixed number of consumers that we're distributing to
  ScopedLockIPC streamLock(streamInterface_->streamLock);

  {
    ScopedLockIPC dataLock(streamInterface_->dataLock);
    StreamConfigStampedIPC data(configIn);
    data.timestamp = getCurrentTimeSec();

    streamInterface_->configConsumedCount = 0;
    streamInterface_->config = data;
    streamInterface_->dataUpdate.notify_all();
  }

  // Wait until we hear that all of our consumers have finished
  checkWaitForData([this]() {
    return streamInterface_->configConsumedCount >= streamInterface_->numSubscribers();
  });
}

void StreamProducerIPC::publish(const StreamSampleIPC& sampleIn) {
  if (valid_) {
    publishValid(sampleIn);
  }
}

void StreamProducerIPC::publishValid(const StreamSampleIPC& sampleIn) {
  // Grab the stream lock so no one can join-in on the stream mid-call
  // We want to have a fixed number of consumers that we're distributing to

  ScopedLockIPC lock(streamInterface_->streamLock);
  if (streamInterface_->numSubscribers() > 0) {
    {
      ScopedLockIPC dataLock(streamInterface_->dataLock);
      StreamSampleStampedIPC data(sampleIn);
      data.timestamp = getCurrentTimeSec();

      streamInterface_->sampleConsumedCount = 0;
      streamInterface_->sample = data;
      streamInterface_->dataUpdate.notify_all();
    }

    // Wait until we hear that all of our consumers have finished
    checkWaitForData([this]() {
      return streamInterface_->sampleConsumedCount >= streamInterface_->numSubscribers();
    });
  }
}

void StreamProducerIPC::checkWaitForData(std::function<bool()> test) {
  bool done = false;
  boost::system_time checkDelay =
      boost::get_system_time() + boost::posix_time::milliseconds(TIMEOUT_MILLISECONDS);
  while (!done) {
    std::this_thread::yield();

    {
      ScopedLockIPC dataLock(streamInterface_->dataLock, boost::interprocess::defer_lock);
      if (dataLock.timed_lock(checkDelay)) {
        done = test();
      }
    }
    Framework::validate();
    checkDelay = boost::get_system_time() + boost::posix_time::milliseconds(TIMEOUT_MILLISECONDS);
  }

  // Clear our sample, since we don't want it to latch.
  {
    ScopedLockIPC dataLock(streamInterface_->dataLock);
    streamInterface_->sample = {};
  }
}

} // namespace cthulhu
