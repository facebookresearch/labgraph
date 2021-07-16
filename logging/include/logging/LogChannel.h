// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <fmt/format.h>

#include <logging/LogLevel.h>
#include <logging/Stub.h>

namespace arvr {
namespace logging {
static constexpr const size_t kLogCapacity = 500;

template <typename... Args>
void log(const char* channel, const char* levelName, ::arvr::logging::Level level, Args&&... args) {
  static char buffer[kLogCapacity];

  if (level > static_cast<::arvr::logging::Level>(::arvr::logging::sGlobalLogLevel)) {
    return;
  }

  char* const out = ::fmt::format_to_n(buffer, kLogCapacity, std::forward<Args>(args)...).out;
  int lineLength = out - buffer;
  std::string line(buffer, out + lineLength);

  stubLog("[{}][{}] {}", channel, levelName, line);
}

template <typename... Args>
void logIf(
    bool condition,
    const char* channel,
    const char* levelName,
    ::arvr::logging::Level level,
    Args&&... args) {
  if (!condition) {
    return;
  }
  log(channel, levelName, level, std::forward<Args>(args)...);
}

} // namespace logging
} // namespace arvr

#define XR_LOG_CHANNELNAME(channelName, levelName, level, ...) \
  ::arvr::logging::log(channelName, levelName, level, __VA_ARGS__)

#define XR_LOGCT(channelName, ...) \
  XR_LOG_CHANNELNAME(channelName, "TRACE", ::arvr::logging::Level::Trace, __VA_ARGS__)
#define XR_LOGCD(channelName, ...) \
  XR_LOG_CHANNELNAME(channelName, "DEBUG", ::arvr::logging::Level::Debug, __VA_ARGS__)
#define XR_LOGCI(channelName, ...) \
  XR_LOG_CHANNELNAME(channelName, "INFO", ::arvr::logging::Level::Info, __VA_ARGS__)
#define XR_LOGCW(channelName, ...) \
  XR_LOG_CHANNELNAME(channelName, "WARNING", ::arvr::logging::Level::Warning, __VA_ARGS__)
#define XR_LOGCE(channelName, ...) \
  XR_LOG_CHANNELNAME(channelName, "ERROR", ::arvr::logging::Level::Error, __VA_ARGS__)

#define XR_LOGIF_CHANNELNAME(condition, channelName, levelName, level, ...) \
  ::arvr::logging::logIf(condition, channelName, levelName, level, __VA_ARGS__)

#define XR_LOGCT_IF(condition, channelName, ...) \
  XR_LOGIF_CHANNELNAME(condition, channelName, "TRACE", ::arvr::logging::Level::Trace, __VA_ARGS__)
#define XR_LOGCD_IF(condition, channelName, ...) \
  XR_LOGIF_CHANNELNAME(condition, channelName, "DEBUG", ::arvr::logging::Level::Debug, __VA_ARGS__)
#define XR_LOGCI_IF(condition, channelName, ...) \
  XR_LOGIF_CHANNELNAME(condition, channelName, "INFO", ::arvr::logging::Level::Info, __VA_ARGS__)
#define XR_LOGCW_IF(condition, channelName, ...) \
  XR_LOGIF_CHANNELNAME(                          \
      condition, channelName, "WARNING", ::arvr::logging::Level::Warning, __VA_ARGS__)
#define XR_LOGCE_IF(condition, channelName, ...) \
  XR_LOGIF_CHANNELNAME(condition, channelName, "ERROR", ::arvr::logging::Level::Error, __VA_ARGS__)
