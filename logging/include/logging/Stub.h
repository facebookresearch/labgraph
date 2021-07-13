// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <mutex>

#include <fmt/format.h>

namespace arvr {
namespace logging {

template <typename... Args>
void stubLog(Args&&... args) {
  static std::mutex logMutex;
  std::scoped_lock<std::mutex> logLock(logMutex);

  ::fmt::print(std::forward<Args>(args)...);
}

} // namespace logging
} // namespace arvr
