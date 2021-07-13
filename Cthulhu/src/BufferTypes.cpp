// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/BufferTypes.h>

#include <stdexcept>

namespace cthulhu {

CpuBuffer GpuBuffer::mapped() const {
  return CpuBuffer_;
}

AnyBuffer::operator CpuBuffer() const {
  if (type == BufferType::CPU) {
    return std::get<CpuBuffer>(data);
  } else if (type == BufferType::GPU) {
    return std::get<GpuBuffer>(data).mapped();
  }
  return nullptr;
}

AnyBuffer::operator bool() const {
  if (type == BufferType::CPU) {
    return (bool)std::get<CpuBuffer>(data);
  } else if (type == BufferType::GPU) {
    return (bool)std::get<GpuBuffer>(data);
  }
  return false;
}

AnyBuffer& AnyBuffer::operator=(const CpuBuffer& buffer) {
  data = buffer;
  type = BufferType::CPU;
  return *this;
}

AnyBuffer& AnyBuffer::operator=(const GpuBuffer& buffer) {
  data = buffer;
  type = BufferType::GPU;
  return *this;
}

AnyBuffer::AnyBuffer(const BufferType& _type) : type(_type) {}

AnyBuffer::AnyBuffer(const CpuBuffer& buffer) : data(buffer), type(BufferType::CPU) {}

AnyBuffer::AnyBuffer(const GpuBuffer& buffer) : data(buffer), type(BufferType::GPU) {}

} // namespace cthulhu
