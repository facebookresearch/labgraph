// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

// Boost interpeocess uses date_time, which needs separable compilation
// Interprocess doesn't need this part of date_time, so disable
#define BOOST_DATE_TIME_NO_LIB

// If anyone else has included interprocess_mutex.hpp,
// we must stop them. These changes need to be applied.
#if defined(BOOST_INTERPROCESS_MUTEX_HPP)
#error Must include Cthulhu's IPCEssentials.h before boost's interprocess_mutex.hpp
#endif

#ifdef _WIN32
// Note: By default, boost will use spin_mutex on Windows, which
// is much slower than native windows mutex. It uses atomic CAS
// on a shared address repeatedly until it works, which isn't
// great for performance
#include <boost/interprocess/detail/workaround.hpp>
#undef BOOST_INTERPROCESS_FORCE_GENERIC_EMULATION

#include <boost/interprocess/managed_windows_shared_memory.hpp>
#elif defined(__ANDROID__)
#define BOOST_INTERPROCESS_BUGGY_POSIX_PROCESS_SHARED
#include "boost/interprocess/managed_android_shared_memory.hpp"
#else
#include <boost/interprocess/managed_shared_memory.hpp>
#endif

#include <boost/interprocess/containers/string.hpp>
#include <boost/interprocess/smart_ptr/shared_ptr.hpp>
#include <boost/interprocess/sync/interprocess_condition.hpp>
#include <boost/interprocess/sync/interprocess_mutex.hpp>
#include <boost/interprocess/sync/scoped_lock.hpp>

#if defined(__APPLE__) // T74434280
#include <boost/interprocess/mem_algo/simple_seq_fit.hpp>
#include <boost/interprocess/sync/mutex_family.hpp>
#endif

#include <cthulhu/BufferTypes.h>

namespace cthulhu {

// Sync types
using MutexIPC = boost::interprocess::interprocess_mutex;
using ConditionIPC = boost::interprocess::interprocess_condition;
using ScopedLockIPC = boost::interprocess::scoped_lock<MutexIPC>;

// Shmem types
#ifdef _WIN32
using ManagedSHM = boost::interprocess::managed_windows_shared_memory;
#elif defined(__ANDROID__)
using ManagedSHM = boost::interprocess::managed_android_shared_memory;
#elif defined(__APPLE__) // T74434280
using ManagedSHM = boost::interprocess::basic_managed_shared_memory<
    char,
    boost::interprocess::simple_seq_fit<boost::interprocess::mutex_family>,
    boost::interprocess::iset_index>;
#else
using ManagedSHM = boost::interprocess::managed_shared_memory;
#endif

using CharAllocatorIPC = boost::interprocess::allocator<char, ManagedSHM::segment_manager>;
using StreamIDIPC =
    boost::interprocess::basic_string<char, std::char_traits<char>, CharAllocatorIPC>;

struct MemoryPoolIPC;
struct MemoryPoolGPUIPC;

// Ptr types
using PtrAllocatorIPC = boost::interprocess::allocator<void, ManagedSHM::segment_manager>;

class ReclaimerIPC {
 public:
  typedef typename boost::intrusive::pointer_traits<
      typename ManagedSHM::segment_manager::void_pointer>::template rebind_pointer<uint8_t>::type
      pointer;

 private:
  boost::interprocess::offset_ptr<MemoryPoolIPC> host;
  std::ptrdiff_t offset;

 public:
  ReclaimerIPC(boost::interprocess::offset_ptr<MemoryPoolIPC> phost, std::ptrdiff_t off)
      : host(phost), offset(off) {}

  void operator()(const pointer& p);
};

using GpuBufferDataWithPID = std::pair<GpuBufferData, uint64_t>;

class ReclaimerGPUIPC {
 public:
  typedef typename boost::intrusive::
      pointer_traits<typename ManagedSHM::segment_manager::void_pointer>::template rebind_pointer<
          GpuBufferDataWithPID>::type pointer;

 private:
  boost::interprocess::offset_ptr<MemoryPoolIPC> host;
  std::ptrdiff_t offset;

 public:
  ReclaimerGPUIPC(boost::interprocess::offset_ptr<MemoryPoolIPC> phost, std::ptrdiff_t off)
      : host(phost), offset(off) {}

  void operator()(const pointer& p);
};

using SharedPtrIPC = boost::interprocess::shared_ptr<uint8_t, PtrAllocatorIPC, ReclaimerIPC>;
using SharedPtrGPUIPC =
    boost::interprocess::shared_ptr<GpuBufferDataWithPID, PtrAllocatorIPC, ReclaimerGPUIPC>;

} // namespace cthulhu
