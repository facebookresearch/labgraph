// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <mutex>
#include <unordered_map>

#include "AuditorIPC.h"
#include "MemoryPoolIPC.h"

#include <cthulhu/MemoryPoolInterface.h>
#include <cthulhu/VulkanUtil.h>

namespace cthulhu {

class MemoryPool;
struct MemoryPoolIPC;

class MemoryPoolIPCHybrid : public MemoryPoolInterface {
 public:
  MemoryPoolIPCHybrid(ManagedSHM* shm, size_t shmSize, size_t shmGPUSize, bool enableAuditor);
  virtual ~MemoryPoolIPCHybrid();

  virtual CpuBuffer getBufferFromPool(const StreamIDView& id, size_t nrBytes) override;

  virtual GpuBuffer getGpuBufferFromPool(size_t nrBytes, bool deviceLocal) override;

  virtual bool isBufferFromPool(const AnyBuffer& buf) const override;

  // Gets the underlying IPC shared pointer for a local pointer
  // Returns null if the pointer did not come from this pool of shared memory buffers
  SharedPtrIPC convert(const CpuBuffer& ptr) const;
  SharedPtrGPUIPC convert(const GpuBuffer& ptr) const;

  CpuBuffer createLocal(const SharedPtrIPC& buffer);
  GpuBuffer createLocal(const SharedPtrGPUIPC& buffer);

  // Toggles whether a particular stream will actively allocate data from shared memory
  // for IPC. If false, it will use local memory buffers.
  void activateStream(const StreamIDView& streamID, bool active);

  SharedPtrIPC getBufferFromSharedPoolDirect(size_t nrBytes);

  // Destroy the framework without any concern for other Cthulhu users
  //
  // Intended to be used as last-resort cleanup of a misbehaving Cthulhu framework.
  // Users should typically favor cleanup().
  static bool nuke(ManagedSHM* shm);

  // Test whether the current section has not been invalidated, and that all of the
  // connected processes are still alive.
  //
  // This will return true if the current state of the pool is valid.
  bool isValid() const override;

  // Mark this section as killed
  //
  // This serves as an indication to any attached processes that the section is no longer
  // valid and should be disconnected from as soon as possible, with no further interactions.
  void invalidate() override;

 private:
  // when audit fails, this section is toast
  bool audit() const;

  bool processesAlive() const;

  void destroyLocal(uint8_t* ptr);
  void destroyLocal(GpuBufferData* ptr);

  void cleanPool(boost::interprocess::offset_ptr<MemoryPoolIPC> pool, bool clearAllocations);

  bool findBuffer(
      size_t nrBytes,
      boost::interprocess::offset_ptr<MemoryPoolIPC> pool,
      std::ptrdiff_t& offset_ptr_out,
      GpuBufferDataWithPID*& ptr_out);

  CpuBuffer requestSHM(size_t nrBytes);

  boost::interprocess::offset_ptr<bool> killSignal_;

  boost::interprocess::offset_ptr<MemoryPoolIPC> pool_;
  std::unordered_map<uint8_t*, SharedPtrIPC> ptrs_;

  boost::interprocess::offset_ptr<MemoryPoolIPC> poolGPU_;
  boost::interprocess::offset_ptr<MemoryPoolIPC> poolGPUDeviceLocal_;
  std::unordered_map<uint64_t, uint64_t> gpuHandleProcMap_;
  std::unordered_map<uint64_t, SharedPtrGPUIPC> handlesGPU_;
  std::unordered_map<uint64_t, std::shared_ptr<uint8_t>> gpuMappedBuffers_;

  size_t shmSize_;
  uint64_t shmGPUSize_;

  std::unique_ptr<MemoryPool> memoryPool_;
  mutable std::mutex memoryMutex_;

  ManagedSHM* shm_;

  std::map<StreamIDView, bool> activatedStreams_;

  // The auditor shared object and associated local data.
  // This should be moved out of memory pool and into its own object
  // in FrameworkIPCHybrid
  boost::interprocess::offset_ptr<AuditorIPC> auditor_;
  std::thread auditorThread_;
  std::atomic<bool> stopSignal_;

  std::unique_ptr<VulkanUtil> vulkanUtil_;

  // The percentage of Cthulhu's shared memory that is permitted to be occupied
  // by the memory pool.
  static constexpr float MAX_SHM_USAGE_FRAC = 0.9;
};

} // namespace cthulhu
