// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/bindings/cuda_util.h>

#ifdef _WIN32
#include <windows.h>
#endif

#ifdef CTHULHU_HAS_CUDA
#include <cuda_runtime.h>
#endif

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

CudaUtil::~CudaUtil() {
  for (auto& handle : cudaHandleCache_) {
    free(handle.second.first, handle.second.second);
  }
}

uint64_t CudaUtil::mapExternalMemoryHandle(uint64_t handle, uint32_t allocatedSize) {
#ifdef CTHULHU_HAS_CUDA
  if (cudaHandleCache_.find(handle) != cudaHandleCache_.end()) {
    return cudaHandleCache_[handle].first;
  }

  // import memory
  cudaExternalMemoryHandleDesc memDesc = {};
#ifdef _WIN32
  memDesc.type = cudaExternalMemoryHandleTypeOpaqueWin32;
  memDesc.handle.win32.handle = (HANDLE)handle;
#else
  memDesc.type = cudaExternalMemoryHandleTypeOpaqueFd;
  memDesc.handle.fd = (int)handle;
#endif
  memDesc.size = allocatedSize;

  cudaExternalMemory_t externalMem{};
  if (auto ret = cudaImportExternalMemory(&externalMem, &memDesc); ret != cudaSuccess) {
    XR_LOGW("Cannot import external memory {}, error code: {}", handle, std::to_string(ret));
    return 0;
  }
  cudaExternalMemoryBufferDesc externalMemBufferDesc = {};
  externalMemBufferDesc.offset = 0;
  externalMemBufferDesc.size = memDesc.size;
  externalMemBufferDesc.flags = 0;
  uint8_t* ptr = nullptr;
  if (auto ret =
          cudaExternalMemoryGetMappedBuffer((void**)&ptr, externalMem, &externalMemBufferDesc);
      ret != cudaSuccess) {
    XR_LOGW("Cannot map external memory {}, error code: {}", handle, std::to_string(ret));
    return 0;
  }

  // Cache the result
  std::pair<uint64_t, uint64_t> result = {(uint64_t)ptr, (uint64_t)externalMem};
  cudaHandleCache_[handle] = result;

  return result.first;
#else
  XR_LOGW("Failed to map external memory handle to CUDA. CUDA support was not included in build.");
  return 0;
#endif
}

void CudaUtil::free(uint64_t mappedHandle, uint64_t externalMem) {
#ifdef CTHULHU_HAS_CUDA
  cudaDestroyExternalMemory((cudaExternalMemory_t)externalMem);
  cudaFree((uint8_t*)mappedHandle);
#endif
}

CudaUtil& CudaUtil::instance() {
  static CudaUtil util;
  return util;
}

} // namespace cthulhu
