// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cstdint>
#include <functional>
#include <memory>
#include <variant>

namespace cthulhu {

enum class BufferType : uint8_t {
  NULL_BUFFER,
  CPU,
  GPU,
};

using CpuBuffer = std::shared_ptr<uint8_t>;

struct GpuBufferData {
  uint64_t handle = 0;
  uint32_t size = 0;
  uint32_t memoryTypeIndex = 0;
};

/**
 * A GPU Buffer is a ref-counted pointer to an opaque
 * platform-specific Vulkan exported memory handle type.
 * It contains a convenience function for mapping to an equivalent
 * host memory buffer with shared reference count.
 */
class GpuBuffer : public std::shared_ptr<GpuBufferData> {
 public:
  GpuBuffer() = default;
  GpuBuffer(
      GpuBufferData* ptr,
      const std::function<void(GpuBufferData*)>& deleter,
      const CpuBuffer& CpuBuffer)
      : std::shared_ptr<GpuBufferData>(ptr, deleter), CpuBuffer_(CpuBuffer) {}

  // GPU Buffers may be host-visible, and can be mapped or copied to
  // the CPU address space as needed.
  CpuBuffer mapped() const;

 private:
  // The function used to map to a CpuBuffer
  CpuBuffer CpuBuffer_;
};

/**
 * Common storage for either CPU or GPU based buffers.
 */
struct AnyBuffer {
  AnyBuffer() = default;

  AnyBuffer(const BufferType& _type);

  AnyBuffer(const CpuBuffer& buffer);

  AnyBuffer(const GpuBuffer& buffer);

  AnyBuffer& operator=(const CpuBuffer& buffer);

  AnyBuffer& operator=(const GpuBuffer& buffer);

  // Will automatically cast to a CpuBuffer, by mapping a GpuBuffer
  // if needed.
  operator CpuBuffer() const;

  // Returns true if data is not a nullptr.
  operator bool() const;

  std::variant<CpuBuffer, GpuBuffer> data;
  BufferType type = BufferType::NULL_BUFFER;
};

} // namespace cthulhu
