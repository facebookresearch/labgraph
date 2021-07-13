// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include "ClockLocal.h"

#include <cthulhu/ClockManagerInterface.h>

namespace cthulhu {

class ClockManagerLocal : public ClockManagerInterface {
 public:
  virtual const std::shared_ptr<ControllableClockInterface> controlClock(
      const std::string& contextName) override;

  inline virtual const std::shared_ptr<ClockInterface> clock() override {
    if (state_ == ClockManagerState::UNKNOWN) {
      return std::shared_ptr<ClockInterface>();
    }
    if (!clock_) {
      if (state_ == ClockManagerState::REAL) {
        clock_ = std::make_shared<ClockLocal>();
      } else {
        clock_ = std::make_shared<ControllableClockLocal>();
      }
    }
    return clock_;
  };

  virtual ~ClockManagerLocal() = default;

 protected:
  virtual void setClockAuthority(bool simTime = false, const std::string& authorizedContext = "")
      override;

 private:
  // The Clock
  std::shared_ptr<ClockInterface> clock_;
  std::string clockOwnerContext_;
};

} // namespace cthulhu
