// Copyright 2004-present Facebook. All Rights Reserved.

#include "MemoryPoolLocal.h"

#include "MemoryPoolLocalImpl.h"

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

MemoryPoolLocal::MemoryPoolLocal()
    : memoryPool_(new MemoryPool()), allocatedGPU_(0), allocatedMaxGPU_(500 * 1024 * 1024) {
  vulkanUtil_.reset(new VulkanUtil());
}

MemoryPoolLocal::~MemoryPoolLocal() {
  // Cleanup GPU Pool
  for (auto& GpuBufferSizeClass : GpuBuffers_) {
    for (auto& GpuBuffer : GpuBufferSizeClass.second) {
      vulkanUtil_->free(GpuBuffer.handle);
    }
  }
}

CpuBuffer MemoryPoolLocal::getBufferFromPool(const StreamIDView& id, size_t nrBytes) {
  return memoryPool_->request(nrBytes);
};

GpuBuffer MemoryPoolLocal::getGpuBufferFromPool(size_t nrBytes, bool deviceLocal) {
  if (!vulkanUtil_->isActive()) {
    XR_LOGW("Failed to generate GPU Buffer. Vulkan is not active.");
    return GpuBuffer();
  }

  // Try to find an existing buffer
  GpuBufferData existing;
  if (findBufferData(nrBytes, deviceLocal ? GpuDeviceLocalBuffers_ : GpuBuffers_, existing)) {
    return createGpuBuffer(existing);
  }

  if (allocatedMaxGPU_ <= allocatedGPU_ + nrBytes) {
    XR_LOGW("Failed to allocate GPU buffer, reached allocated max: {}", allocatedMaxGPU_);
    return GpuBuffer();
  }

  // Allocate a new buffer
  auto vulkanAllocation = vulkanUtil_->allocate(nrBytes, deviceLocal);
  if (vulkanAllocation.first == 0) {
    return GpuBuffer();
  }
  GpuBufferData result;
  result.handle = vulkanAllocation.first;
  result.size = nrBytes;
  result.memoryTypeIndex = vulkanAllocation.second;

  allocatedGPU_ += nrBytes;

  // Store a local map of the external memory, which adds a reference for the local process
  if (!deviceLocal) {
    gpuMappedBuffers_[vulkanAllocation.first] =
        vulkanUtil_->map(vulkanAllocation.first, nrBytes, vulkanAllocation.second);
  }

  return createGpuBuffer(result);
}

void MemoryPoolLocal::reclaimGPU(const GpuBufferData* ptr) {
  {
    std::lock_guard<std::mutex> lock(GpuBuffersMutex_);
    bool deviceLocal = vulkanUtil_->isDeviceLocal(ptr->memoryTypeIndex);
    auto bufferIt =
        deviceLocal ? GpuDeviceLocalBuffers_.find(ptr->size) : GpuBuffers_.find(ptr->size);
    auto& bufferList = bufferIt->second;
    bufferList.push_back(*ptr);
  }
}

bool MemoryPoolLocal::isBufferFromPool(const AnyBuffer& buf) const {
  return true;
}

size_t MemoryPoolLocal::getMaxSizeBytes() const noexcept {
  return MemoryPool::ALLOCATED_MAX_BYTES;
}

GpuBuffer MemoryPoolLocal::createGpuBuffer(const GpuBufferData& data) {
  return GpuBuffer(
      new GpuBufferData(data),
      [this](const GpuBufferData* ptr) -> void { reclaimGPU(ptr); },
      vulkanUtil_->isDeviceLocal(data.memoryTypeIndex) ? CpuBuffer()
                                                       : gpuMappedBuffers_[data.handle]);
}

bool MemoryPoolLocal::findBufferData(size_t nrBytes, GpuBuffers& buffers, GpuBufferData& out) {
  std::lock_guard<std::mutex> lock(GpuBuffersMutex_);
  auto bufferIt = buffers.find(nrBytes);
  if (bufferIt == buffers.cend()) {
    bufferIt = buffers.emplace(nrBytes, std::vector<GpuBufferData>()).first;
  }

  auto& bufferList = bufferIt->second;
  if (!bufferList.empty()) {
    out = bufferList.back();
    bufferList.pop_back();
    return true;
  }
  return false;
}

} // namespace cthulhu
