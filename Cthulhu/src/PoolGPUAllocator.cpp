// Copyright 2004-present Facebook. All Rights Reserved.

#include "PoolGPUAllocator.h"

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

bool PoolGPUAllocator::findBuffer(
    size_t nrBytes,
    std::ptrdiff_t& offset_ptr_out,
    SharedGpuBufferData*& ptr_out) {
  ScopedLockIPC lock(pool_->buffers_mutex);
  auto buffer_it = pool_->buffers.find(nrBytes);
  if (buffer_it == pool_->buffers.cend()) {
    buffer_it = pool_->buffers
                    .emplace(
                        nrBytes,
                        MemoryPoolIPC::PtrVectorType(
                            MemoryPoolIPC::PtrVectorAllocType(shm_->get_segment_manager())))
                    .first;
  }

  auto& ptrlist = buffer_it->second;
  // Iterate through the list until we find one that originated from our process.
  // Note: It may be useful to restructure our GPU pool to make it faster to find
  // buffers originating from our process.
#ifdef _WIN32
  uint64_t ourPid = (uint64_t)GetCurrentProcessId();
#else
  uint64_t ourPid = (uint64_t)getpid();
#endif
  auto it = ptrlist.begin();
  while (it != ptrlist.end()) {
    auto bufferData = reinterpret_cast<SharedGpuBufferData*>(shm_->get_address_from_handle(*it));
    if (bufferData->pid == ourPid) {
      ptr_out = bufferData;
      offset_ptr_out = *it;
      it = ptrlist.erase(it);
      return true;
    } else {
      ++it;
    }
  }
  return false;
}

bool PoolGPUAllocator::getBuffer(
    size_t nrBytes,
    bool allocate,
    std::ptrdiff_t& offset_ptr_out,
    SharedGpuBufferData*& buffer_out,
    std::shared_ptr<uint8_t>& mapped_out) {
  return findBuffer(nrBytes, offset_ptr_out, buffer_out) ||
      (allocate && allocateBuffer(nrBytes, offset_ptr_out, buffer_out, mapped_out));
}

bool PoolGPUAllocator::allocateBuffer(
    size_t nrBytes,
    std::ptrdiff_t& offset_ptr_out,
    SharedGpuBufferData*& bufferData_out,
    std::shared_ptr<uint8_t>& mapped_out) {
  // Make a new buffer
  ScopedLockIPC lock(pool_->sizes_mutex);
  if (deviceLocal_) {
    XR_LOGT_EVERY_N(
        10, "MemoryPoolIPCHybrid - Num GPU Device Local bytes allocated: ", pool_->allocated);
  } else {
    XR_LOGT_EVERY_N(10, "MemoryPoolIPCHybrid - Num GPU bytes allocated: ", pool_->allocated);
  }
  auto vulkanAllocation = vulkanUtil_->allocate(nrBytes, deviceLocal_);
  if (vulkanAllocation.first == 0) {
    XR_LOGW("Failed to allocate vulkan buffer of size {}.", nrBytes);
    return false;
  }
  // Store a local map of the external memory, which adds a reference for the local process
  mapped_out = vulkanUtil_->map(vulkanAllocation.first, nrBytes, vulkanAllocation.second);
#ifdef _WIN32
  uint64_t pid = (uint64_t)GetCurrentProcessId();
#else
  uint64_t pid = (uint64_t)getpid();
#endif
  // Put the handle in shared memory
  bufferData_out = shm_->construct<SharedGpuBufferData>(boost::interprocess::anonymous_instance)();
  bufferData_out->handle = vulkanAllocation.first;
  bufferData_out->size = nrBytes;
  bufferData_out->memoryTypeIndex = vulkanAllocation.second;
  bufferData_out->pid = pid;
  offset_ptr_out = shm_->get_handle_from_address(bufferData_out);
  pool_->allocated += nrBytes;
  pool_->sizes.emplace(offset_ptr_out, nrBytes);
  return true;
}

} // namespace cthulhu
