// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/ClockManagerInterface.h>
#include "ClockIPC.h"

#include <boost/interprocess/containers/string.hpp>

namespace cthulhu {

typedef boost::interprocess::basic_string<char, std::char_traits<char>, CharAllocatorIPC>
    ContextIPC;

struct ClockManagerIPCData {
 public:
  ClockManagerIPCData(const CharAllocatorIPC& alloc) : clockOwnerContext(alloc) {}

  ContextIPC clockOwnerContext;
  MutexIPC lock;
  ClockIPCData clock;
  uint32_t reference_count = 0;
  ClockManagerState state = ClockManagerState::UNKNOWN;
};

class ClockManagerIPC : public ClockManagerInterface {
 public:
  ClockManagerIPC(ManagedSHM* shm);

  virtual ~ClockManagerIPC();

  virtual const std::shared_ptr<ControllableClockInterface> controlClock(
      const std::string& contextName) override;

  virtual const std::shared_ptr<ClockInterface> clock() override;

  // Destroy the framework without any concern for other Cthulhu users
  //
  // Intended to be used as last-resort cleanup of a misbehaving Cthulhu framework.
  // Users should typically favor cleanup().
  static bool nuke(ManagedSHM* shm);

 protected:
  virtual void setClockAuthority(bool simTime = false, const std::string& authorizedContext = "")
      override;

 private:
  ManagedSHM* shm_;

  ClockManagerIPCData* data_ = nullptr;

  mutable std::shared_ptr<ClockIPC> clock_handle_;
};

} // namespace cthulhu
