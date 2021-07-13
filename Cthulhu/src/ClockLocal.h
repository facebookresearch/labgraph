// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/Clock.h>

#include <atomic>

namespace cthulhu {

class ClockLocal : public ClockInterface {
 public:
  ClockLocal(bool simTime = false) : simTime_(simTime), paused_(simTime_), latestTime_(0.) {}
  virtual ~ClockLocal() = default;

  virtual double getTime() override;

  virtual inline bool isSimulated() const override {
    return simTime_;
  }

 protected:
  virtual void updateTime() override;
  virtual void updateLatestTime(double desired, double reference, bool enableBackwards = false)
      override;

  bool simTime_;
  bool paused_;
  double realtimeFactor_ = 1.;
  double offset_ = 0.0; // offset of the output time from the wallStartTime
  double wallStartTime_ = 0.0; // beginning of the time axis in wall time
  std::atomic<double> latestTime_;
};

class ControllableClockLocal : public ControllableClockInterface, public ClockLocal {
 public:
  ControllableClockLocal() : ClockLocal(true) {}
  virtual ~ControllableClockLocal() = default;

  virtual bool start(double time = -1.) override;
  virtual void pause() override;
  virtual bool setRealtimeFactor(double rtf) override;
  virtual bool setTime(double time) override;
};

} // namespace cthulhu
