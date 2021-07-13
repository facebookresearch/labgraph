// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <memory>
#include <string>

#include <cthulhu/Clock.h>
#include <cthulhu/ForceCleanable.h>
#include <cthulhu/LogDisabling.h>

namespace cthulhu {

class ClockAuthority;

enum class ClockManagerState : uint8_t {
  UNKNOWN = 0,
  REAL = 1,
  SIM = 2,
};

class ClockManagerInterface : public ForceCleanable, public LogDisabling {
 public:
  virtual const std::shared_ptr<ControllableClockInterface> controlClock(
      const std::string& contextName) = 0;
  virtual const std::shared_ptr<ClockInterface> clock() = 0;

  virtual ~ClockManagerInterface() = default;

 protected:
  // A simulated clock must have an owning context. This is the interface for
  // creating a simulated clock, and specifying that owner
  virtual void setClockAuthority(
      bool simTime = false,
      const std::string& authorizedContext = "") = 0;

  ClockManagerState state_;

  friend class ClockAuthority;
};

} // namespace cthulhu
