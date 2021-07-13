// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <logging/LogChannel.h>
#include <logging/LogLevel.h>

#ifndef DEFAULT_LOG_CHANNEL
#error "DEFAULT_LOG_CHANNEL must be defined before including <logging/Log.h>"
#endif // DEFAULT_LOG_CHANNEL

#define XR_LOG_DEFAULT(levelName, level, ...) \
  XR_LOG_CHANNELNAME(DEFAULT_LOG_CHANNEL, levelName, level, __VA_ARGS__)

#define XR_LOGT(...) XR_LOG_DEFAULT("TRACE", ::arvr::logging::Level::Trace, __VA_ARGS__)
#define XR_LOGD(...) XR_LOG_DEFAULT("DEBUG", ::arvr::logging::Level::Debug, __VA_ARGS__)
#define XR_LOGI(...) XR_LOG_DEFAULT("INFO", ::arvr::logging::Level::Info, __VA_ARGS__)
#define XR_LOGW(...) XR_LOG_DEFAULT("WARNING", ::arvr::logging::Level::Warning, __VA_ARGS__)
#define XR_LOGE(...) XR_LOG_DEFAULT("ERROR", ::arvr::logging::Level::Error, __VA_ARGS__)

#define XR_LOGT_EVERY_N_SEC(n, ...) XR_LOGT(__VA_ARGS__)
#define XR_LOGD_EVERY_N_SEC(n, ...) XR_LOGD(__VA_ARGS__)
#define XR_LOGI_EVERY_N_SEC(n, ...) XR_LOGI(__VA_ARGS__)
#define XR_LOGW_EVERY_N_SEC(n, ...) XR_LOGW(__VA_ARGS__)
#define XR_LOGE_EVERY_N_SEC(n, ...) XR_LOGE(__VA_ARGS__)

#define XR_LOGT_EVERY_N(n, ...) XR_LOGT(__VA_ARGS__)
#define XR_LOGD_EVERY_N(n, ...) XR_LOGD(__VA_ARGS__)
#define XR_LOGI_EVERY_N(n, ...) XR_LOGI(__VA_ARGS__)
#define XR_LOGW_EVERY_N(n, ...) XR_LOGW(__VA_ARGS__)
#define XR_LOGE_EVERY_N(n, ...) XR_LOGE(__VA_ARGS__)

#define XR_LOGT_ONCE(...) XR_LOGT(__VA_ARGS__)
#define XR_LOGD_ONCE(...) XR_LOGD(__VA_ARGS__)
#define XR_LOGI_ONCE(...) XR_LOGI(__VA_ARGS__)
#define XR_LOGW_ONCE(...) XR_LOGW(__VA_ARGS__)
#define XR_LOGE_ONCE(...) XR_LOGE(__VA_ARGS__)
