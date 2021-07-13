// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#ifdef _WIN32
#include <windows.h>
#endif
#include <mutex>

#include "IPCEssentials.h"

#include <boost/interprocess/containers/map.hpp>
#include <boost/interprocess/containers/vector.hpp>

namespace cthulhu {

struct MemoryPoolIPC {
  friend class ReclaimerIPC;
  friend class ReclaimerGPUIPC;

  typedef boost::interprocess::allocator<std::ptrdiff_t, ManagedSHM::segment_manager>
      PtrVectorAllocType;
  typedef boost::interprocess::vector<std::ptrdiff_t, PtrVectorAllocType> PtrVectorType;

  typedef boost::interprocess::
      allocator<std::pair<const size_t, PtrVectorType>, ManagedSHM::segment_manager>
          BufferMapAllocType;
  typedef boost::interprocess::map<size_t, PtrVectorType, std::less<size_t>, BufferMapAllocType>
      BufferMapType;

  typedef boost::interprocess::allocator<std::pair<const int, size_t>, ManagedSHM::segment_manager>
      SizeMapAllocType;
  typedef boost::interprocess::map<int, size_t, std::less<int>, SizeMapAllocType> SizeMapType;

  MemoryPoolIPC(ManagedSHM::segment_manager* mgr) : buffers(mgr), sizes(mgr) {}

  BufferMapType buffers;
  MutexIPC buffers_mutex;

  SizeMapType sizes;
  MutexIPC sizes_mutex;

  std::atomic<size_t> allocated;

 private:
  void reclaim(std::ptrdiff_t off);
};

} // namespace cthulhu
