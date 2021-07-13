// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/StreamInterface.h>
#include <cthulhu/TypeRegistryInterface.h>

namespace cthulhu {

// Returns whether two StreamConfigs are equal given the type information of the stream associated
// with the config type that these StreamConfigs back.
bool streamConfigsEqual(
    const StreamConfig& lhs,
    const StreamConfig& rhs,
    const TypeInfoInterface& stream_type_info);

} // namespace cthulhu
