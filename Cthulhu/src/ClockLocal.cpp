// Copyright 2004-present Facebook. All Rights Reserved.

#include "ClockLocal.h"

#include <logging/LogChannel.h>

namespace cthulhu {

double ClockLocal::getTime() {
  if (simTime_) {
    if (!paused_)
      updateTime();
    return latestTime_;
  }
  return getWallTime();
}

void ClockLocal::updateTime() {
  double reference = latestTime_;
  double wall = getWallTime();
  updateLatestTime(realtimeFactor_ * (wall - wallStartTime_) + offset_, reference);
}

void ClockLocal::updateLatestTime(double desired, double reference, bool enableBackwards) {
  double latest;
  do {
    latest = latestTime_;
    if (latest < reference) {
      break;
    }
    if ((enableBackwards && latest == desired) || (!enableBackwards && latest > desired)) {
      break;
    }
  } while (!latestTime_.compare_exchange_weak(latest, desired));
}

bool ControllableClockLocal::start(double time) {
  if (!simTime_) {
    XR_LOGCI("Cthulhu", "Could not start clock, using real time.");
    return false;
  }
  double reference = latestTime_;
  if (!paused_) {
    XR_LOGCI("Cthulhu", "Could not start clock that is currently running.");
    return false;
  }

  updateLatestTime(time, reference, true);

  wallStartTime_ = getWallTime();
  if (time >= 0.) {
    offset_ = time;
    for (const auto& listener : listeners_) {
      listener(ClockEvent::JUMP);
    }
  } else {
    offset_ = latestTime_;
  }
  paused_ = false;
  for (const auto& listener : listeners_) {
    listener(ClockEvent::START);
  }
  return true;
}

void ControllableClockLocal::pause() {
  if (!simTime_) {
    XR_LOGCI("Cthulhu", "Could not pause clock, using real time.");
    return;
  }
  if (paused_) {
    XR_LOGCW("Cthulhu", "Could not pause clock while already paused");
    return;
  }
  updateTime();
  paused_ = true;
  for (const auto& listener : listeners_) {
    listener(ClockEvent::PAUSE);
  }
}

bool ControllableClockLocal::setRealtimeFactor(double rtf) {
  if (!simTime_) {
    XR_LOGCW("Cthulhu", "Could not set clock real time factor, using real time.");
    return false;
  }
  if (!paused_) {
    XR_LOGCW("Cthulhu", "Could not set clock real time factor while running");
    return false;
  }
  realtimeFactor_ = rtf;
  for (const auto& listener : listeners_) {
    listener(ClockEvent::RTF_UPDATE);
  }
  return true;
}

bool ControllableClockLocal::setTime(double time) {
  if (!simTime_) {
    XR_LOGCW("Cthulhu", "Could not set clock time, using real time.");
    return false;
  }
  double reference = latestTime_;
  if (!paused_) {
    XR_LOGCW("Cthulhu", "Could not set clock time while running");
    return false;
  }
  updateLatestTime(time, reference, true);
  for (const auto& listener : listeners_) {
    listener(ClockEvent::JUMP);
  }
  return true;
}

} // namespace cthulhu
