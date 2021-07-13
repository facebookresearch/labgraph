// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/Clock.h>

#include <chrono>

namespace cthulhu {

double ClockInterface::getWallTime() const {
  const auto now = std::chrono::high_resolution_clock::now();
  const auto seconds =
      std::chrono::duration<double, std::chrono::seconds::period>(now.time_since_epoch());
  return seconds.count();
}

} // namespace cthulhu
