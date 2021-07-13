// Copyright 2004-present Facebook. All Rights Reserved.

#include "ClockIPC.h"

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

#include <boost/thread/thread_time.hpp>

namespace cthulhu {

ClockIPC::ClockIPC(ClockIPCData* data, bool simTime) : data_(data), simTime_(simTime) {}

ClockIPC::~ClockIPC() = default;

double ClockIPC::getTime() {
  if (simTime_) {
    if (!data_->paused)
      // advance time
      updateTime();
    return data_->latestTime;
  }
  return getWallTime();
}

void ClockIPC::updateTime() {
  double reference = data_->latestTime;
  double wall = getWallTime();
  updateLatestTime(
      data_->realtimeFactor * (wall - data_->wallStartTime) + data_->offset, reference);
}

void ClockIPC::updateLatestTime(double desired, double reference, bool enableBackwards) {
  double latest;
  do {
    latest = data_->latestTime;
    if (latest < reference) {
      break;
    }
    if ((enableBackwards && latest == desired) || (!enableBackwards && latest > desired)) {
      break;
    }
  } while (!data_->latestTime.compare_exchange_weak(latest, desired));
}

ControllableClockIPC::ControllableClockIPC(ClockIPCData* data)
    : ClockIPC(data, true), localControl_(false) {
  thread_ = std::thread(
      [this](std::future<void> signal) -> void {
        uint32_t latestEvent = 0;
        while (signal.wait_for(std::chrono::microseconds(0)) == std::future_status::timeout) {
          if (latestEvent < this->data_->signal_count) {
            int eventNumber;
            ClockEvent event;
            {
              ScopedLockIPC lock(this->data_->signal_lock);
              eventNumber = this->data_->signal_count;
              event = this->data_->event;
            }
            for (const auto& listener : this->listeners_) {
              listener(event);
            }
            if (eventNumber != latestEvent + 1) {
              XR_LOGW("ClockIPC - Missed events between {} and {}", latestEvent, eventNumber);
            }
            latestEvent = eventNumber;
          }
          ScopedLockIPC lock(this->data_->signal_lock);
          this->data_->signal_update.timed_wait(
              lock, boost::get_system_time() + boost::posix_time::milliseconds(1));
        }
      },
      stopSignal_.get_future());
}

ControllableClockIPC::~ControllableClockIPC() {
  setControlLocal();
}

void ControllableClockIPC::setControlLocal() {
  if (localControl_) {
    return;
  }
  stopSignal_.set_value();
  if (thread_.joinable()) {
    thread_.join();
  }
  localControl_ = true;
}

bool ControllableClockIPC::start(double time) {
  if (!simTime_) {
    XR_LOGI("Could not start clock, using real time.");
    return false;
  }
  double reference = data_->latestTime;
  if (!data_->paused) {
    XR_LOGI("Could not start clock that is currently running.");
    return false;
  }

  updateLatestTime(time, reference, true);

  data_->wallStartTime = getWallTime();
  if (time >= 0.) {
    data_->offset = time;
    for (const auto& listener : listeners_) {
      listener(ClockEvent::JUMP);
    }
    signalEventIPC(ClockEvent::JUMP);
  } else {
    data_->offset = data_->latestTime;
  }
  data_->paused = false;
  for (const auto& listener : listeners_) {
    listener(ClockEvent::START);
  }
  signalEventIPC(ClockEvent::START);
  return true;
}

void ControllableClockIPC::pause() {
  // sanity checks
  if (!simTime_) {
    XR_LOGI("Could not pause clock, using real time.");
    return;
  }
  if (data_->paused) {
    XR_LOGW("Could not pause clock while already paused");
    return;
  }
  // make sure to update time to the moment of pausing it
  updateTime();
  // inform listeners
  data_->paused = true;
  for (const auto& listener : listeners_) {
    listener(ClockEvent::PAUSE);
  }
  signalEventIPC(ClockEvent::PAUSE);
}

bool ControllableClockIPC::setRealtimeFactor(double rtf) {
  if (!simTime_) {
    XR_LOGW("Could not set clock real time factor, using real time.");
    return false;
  }
  if (!data_->paused) {
    XR_LOGW("Could not set clock real time factor while running");
    return false;
  }
  data_->realtimeFactor = rtf;
  for (const auto& listener : listeners_) {
    listener(ClockEvent::RTF_UPDATE);
  }
  signalEventIPC(ClockEvent::RTF_UPDATE);
  return true;
}

bool ControllableClockIPC::setTime(double time) {
  if (!simTime_) {
    XR_LOGW("Could not set clock time, using real time.");
    return false;
  }
  double reference = data_->latestTime;
  if (!data_->paused) {
    XR_LOGW("Could not set clock time while running");
    return false;
  }
  updateLatestTime(time, reference, true);
  for (const auto& listener : listeners_) {
    listener(ClockEvent::JUMP);
  }
  signalEventIPC(ClockEvent::JUMP);
  return true;
}

void ControllableClockIPC::signalEventIPC(const ClockEvent& event) {
  ScopedLockIPC lock(data_->signal_lock);
  data_->event = event;
  data_->signal_count++;
}

} // namespace cthulhu
