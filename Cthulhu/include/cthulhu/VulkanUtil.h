// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cstdint>
#include <memory>

namespace cthulhu {

struct VulkanUtilState;

class VulkanUtil {
 public:
  VulkanUtil();
  virtual ~VulkanUtil();

  VulkanUtil(const VulkanUtil& other) = delete;
  VulkanUtil& operator=(const VulkanUtil& other) = delete;

  // Allocates an external memory handle for a given number of bytes.
  // It always comes from host visible memory, and only supports linear buffers.
  // It returns both an opaque platform-agnostic handle, and the memory type index
  // which was used when memory was allocated. Returns 0 for the handle when fails.
  std::pair<uint64_t, uint32_t> allocate(uint32_t nrBytes, bool deviceLocal);

  // Should be called on an external memory handle by the last process
  // to release the memory. On some platforms, this won't actually do anything.
  void free(uint64_t handle);

  // Maps an external memory handle to a local memory address, with automated cleanup
  // Every process should hold on to one of these to ensure the underlying memory resource
  // isn't released, as on some platforms the handle itself does not hold a reference once
  // imported. Returns nullptr when fails.
  std::shared_ptr<uint8_t> map(uint64_t handle, uint32_t nrBytes, uint32_t memoryTypeIndex);

  // Returns true if Vulkan is available, otherwise this tool won't do anything.
  bool isActive() const;

  bool isDeviceLocal(uint32_t memoryTypeIndex) const;

 private:
  // Hides all Vulkan-specific data storage from the public interface
  VulkanUtilState* state_ = nullptr;

  bool isActive_ = false;
}; // class VulkanAllocator

} // namespace cthulhu
