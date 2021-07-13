// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <functional>
#include <vector>

namespace cthulhu {

enum class ClockEvent : uint32_t {
  START = 0,
  PAUSE = 1,
  RTF_UPDATE = 2,
  JUMP = 3,
};

using ClockEventCallback = std::function<void(const ClockEvent& event)>;

// This encapsulates a real/simulated clock.
class ClockInterface {
 public:
  ClockInterface(){};
  virtual ~ClockInterface() = default;

  virtual double getTime() = 0;

  virtual bool isSimulated() const = 0;

  void listenEvents(const ClockEventCallback& cb) {
    listeners_.push_back(cb);
  };

 protected:
  // this function updates latestTime of the clock
  virtual void updateTime() = 0;

  // This function is used to guarantee that latestTime_ that is returned is always monotonically
  // increasing, even when pause() and getTime() are called in different threads simultaneously
  virtual void updateLatestTime(double desired, double reference, bool enableBackwards = false) = 0;

  double getWallTime() const;

  std::vector<ClockEventCallback> listeners_;
};

// Controllable interface for a simulated clock
class ControllableClockInterface {
 public:
  ControllableClockInterface() {}
  virtual ~ControllableClockInterface() = default;

  // Starts running the clock from a specified time
  // If no time is specified, it starts from the latest time at
  // which the clock was paused
  virtual bool start(double time = -1.) = 0;

  // Pauses the clock
  virtual void pause() = 0;

  // Can only be called while in the paused state
  virtual bool setRealtimeFactor(double rtf) = 0;

  // Can only be called while in the paused state
  virtual bool setTime(double time) = 0;
};

} // namespace cthulhu
