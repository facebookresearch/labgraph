// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/Clock.h>
#include "IPCEssentials.h"

#include <atomic>
#include <future>
#include <thread>

namespace cthulhu {

struct ClockIPCData {
  ClockIPCData() {
    reset();
  }

  // Note: initialize all members in reset()
  bool paused;
  std::atomic<double> latestTime;
  double realtimeFactor;
  double offset; // offset of the output time at start
  double wallStartTime; // beginning of the time axis in wall time

  // These are used to signal events through IPC
  uint32_t signal_count;
  ConditionIPC signal_update;
  mutable MutexIPC signal_lock;
  ClockEvent event;

  // Resets the clock data stored in IPC
  //
  // If there are multiple references to this data, you should hold
  // the signal_lock before calling this method.
  void reset() {
    paused = true;
    latestTime = 0.0;
    realtimeFactor = 1.0;
    offset = 0.0;
    wallStartTime = 0.0;
    signal_count = 0;
  }
};

class ClockIPC : public ClockInterface {
 public:
  ClockIPC(ClockIPCData* data, bool simTime = false);
  virtual ~ClockIPC();

  virtual double getTime() override;

  virtual inline bool isSimulated() const override {
    return simTime_;
  }

 protected:
  virtual void updateTime() override;

  virtual void updateLatestTime(double desired, double reference, bool enableBackwards = false)
      override;

  ClockIPCData* data_;
  bool simTime_;
};

class ControllableClockIPC : public ControllableClockInterface, public ClockIPC {
 public:
  ControllableClockIPC(ClockIPCData* data);
  virtual ~ControllableClockIPC();

  void setControlLocal();

  virtual bool start(double time = -1.) override;
  virtual void pause() override;
  virtual bool setRealtimeFactor(double rtf) override;
  virtual bool setTime(double time) override;

 private:
  void signalEventIPC(const ClockEvent& event);
  bool localControl_;
  std::thread thread_;
  std::promise<void> stopSignal_;
};

} // namespace cthulhu
