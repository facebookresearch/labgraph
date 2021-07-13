// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <mutex>

#include <cthulhu/MemoryPoolInterface.h>
#include <cthulhu/VulkanUtil.h>

namespace cthulhu {

class MemoryPool;

class MemoryPoolLocal : public MemoryPoolInterface {
 public:
  MemoryPoolLocal();
  virtual ~MemoryPoolLocal();

  virtual CpuBuffer getBufferFromPool(const StreamIDView& id, size_t nrBytes) override;
  virtual GpuBuffer getGpuBufferFromPool(size_t nrBytes, bool device_local) override;
  virtual bool isBufferFromPool(const AnyBuffer& buf) const override;

  // Returns the maximum size of the memory pool
  size_t getMaxSizeBytes() const noexcept;

  virtual void invalidate() override {}

  virtual bool isValid() const override {
    return true;
  }

 private:
  typedef std::map<size_t, std::vector<GpuBufferData>> GpuBuffers;

  void reclaimGPU(const GpuBufferData* ptr);

  bool findBufferData(size_t nrBytes, GpuBuffers& buffers, GpuBufferData& out);

  GpuBuffer createGpuBuffer(const GpuBufferData& data);

  // CPU Memory Pool
  std::unique_ptr<MemoryPool> memoryPool_;

  // GPU Memory Pool
  std::unique_ptr<VulkanUtil> vulkanUtil_;

  GpuBuffers GpuBuffers_;
  GpuBuffers GpuDeviceLocalBuffers_;
  std::mutex GpuBuffersMutex_;
  std::unordered_map<uint64_t, std::shared_ptr<uint8_t>> gpuMappedBuffers_;
  std::atomic<size_t> allocatedGPU_;
  const size_t allocatedMaxGPU_;
};

} // namespace cthulhu
