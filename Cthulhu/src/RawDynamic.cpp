// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/RawDynamic.h>

#include <memory>

#include <cthulhu/Framework.h>

namespace cthulhu {

template <>
CpuBuffer RawDynamic<>::getBuffer() const {
  return Framework::instance().memoryPool()->getBufferFromPool("", size());
}

template <>
RawDynamic<>::RawDynamic(CpuBuffer& buf, size_t count)
    : elementCount(count), elementSize(sizeof(uint8_t)) {
  if (Framework::instance().memoryPool()->isBufferFromPool(buf)) {
    raw = buf;
  } else {
    raw = getBuffer();
    std::memcpy(raw.get(), buf.get(), size());
  }
}

} // namespace cthulhu
