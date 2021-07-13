// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <logging/Stub.h>

namespace arvr {
namespace logging {

template <typename Condition, typename... Args>
void check(Condition condition, Args&&... args) {
  if (condition) {
    return;
  }
  stubLog(std::forward<Args>(args)...);
  std::abort();
}

} // namespace logging
} // namespace arvr

#define XR_CHECK(condition, ...) ::arvr::logging::check(condition, __VA_ARGS__)
#define XR_DEV_CHECK(condition, ...) XR_CHECK(condition, __VA_ARGS__)
