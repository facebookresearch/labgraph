// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/VulkanUtil.h>

#include "IPCEssentials.h"
#include "MemoryPoolIPC.h"

namespace cthulhu {

class PoolGPUAllocator {
 public:
  PoolGPUAllocator(
      boost::interprocess::offset_ptr<MemoryPoolIPC> pool,
      ManagedSHM* shm,
      std::shared_ptr<VulkanUtil> vulkanUtil,
      bool deviceLocal)
      : pool_(pool), shm_(shm), vulkanUtil_(vulkanUtil), deviceLocal_(deviceLocal) {}

  bool getBuffer(
      size_t nrBytes,
      bool allocate,
      std::ptrdiff_t& offset_ptr_out,
      SharedGpuBufferData*& buffer_out,
      std::shared_ptr<uint8_t>& mapped_out);

  boost::interprocess::offset_ptr<MemoryPoolIPC> pool() {
    return pool_;
  }

 private:
  bool findBuffer(size_t nrBytes, std::ptrdiff_t& offset_ptr_out, SharedGpuBufferData*& buffer_out);
  bool allocateBuffer(
      size_t nrBytes,
      std::ptrdiff_t& offset_ptr_out,
      SharedGpuBufferData*& buffer_out,
      std::shared_ptr<uint8_t>& mapped_out);

  boost::interprocess::offset_ptr<MemoryPoolIPC> pool_;
  ManagedSHM* shm_;
  std::shared_ptr<VulkanUtil> vulkanUtil_;
  bool deviceLocal_;
};

} // namespace cthulhu
