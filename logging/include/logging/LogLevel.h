// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

namespace arvr {
namespace logging {

/**
 * Predefined log levels which can be extended if needed.
 **/
enum class Level {
  Disabled = 0, ///< Completely suppresses log output. Not available in the logging macros.
  Error = 1, ///<
  Warning = 2,
  Info = 3,
  Debug = 4,
  Trace = 5,
  UseGlobalSettings = 100, ///< Use the global log level instead of a channel override. Not
                           ///< available in the logging macros.
}; // enum class Level

/// The global level is a global variable and thus needs to be defined by the backend
static int sGlobalLogLevel = static_cast<int>(Level::Info);

/**
 * Set the global log level that applies for all channels, unless the channel has separate settings.
 */
inline void setGlobalLogLevel(int level) {
  sGlobalLogLevel = level;
}

inline void setGlobalLogLevel(Level level) {
  setGlobalLogLevel(static_cast<int>(level));
}

/**
 * Returns the current global log level.
 */
inline int globalLogLevel() {
  return sGlobalLogLevel;
}

} // namespace logging
} // namespace arvr
