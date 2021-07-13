// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cstdint>
#include <map>
#include <utility>

namespace cthulhu {

class CudaUtil {
 public:
  ~CudaUtil();
  uint64_t mapExternalMemoryHandle(uint64_t handle, uint32_t allocationSize);
  static CudaUtil& instance();

 private:
  CudaUtil() = default;
  void free(uint64_t mappedHandle, uint64_t externalMemory);

  /**
   *  Cache the imported handles, because it takes several milliseconds to do.
   */
  std::map<uint64_t, std::pair<uint64_t, uint64_t>> cudaHandleCache_;
}; // class CudaUtil

} // namespace cthulhu
