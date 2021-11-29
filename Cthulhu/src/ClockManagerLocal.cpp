// Copyright 2004-present Facebook. All Rights Reserved.

#include "ClockManagerLocal.h"

#include <cassert>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

const std::shared_ptr<ControllableClockInterface> ClockManagerLocal::controlClock(
    const std::string& contextName) {
  if (!clockOwnerContext_.empty() && contextName.compare(clockOwnerContext_) == 0) {
    return std::dynamic_pointer_cast<ControllableClockLocal>(clock());
  }
  XR_LOGCW(
      "Cthulhu", "Could not provide a controllable clock to non-owning context {}", contextName);
  return std::shared_ptr<ControllableClockLocal>();
}

void ClockManagerLocal::setClockAuthority(bool simTime, const std::string& authorizedContext) {
  assert(clockOwnerContext_.empty());
  clockOwnerContext_ = authorizedContext;
  state_ = simTime ? ClockManagerState::SIM : ClockManagerState::REAL;
}

} // namespace cthulhu
