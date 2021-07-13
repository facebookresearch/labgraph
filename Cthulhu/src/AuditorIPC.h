// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#ifdef _WIN32
#include <windows.h>
#endif
#include <mutex>

#include "IPCEssentials.h"

#include <boost/interprocess/containers/vector.hpp>

namespace cthulhu {

struct AuditorIPC {
  struct Process {
    Process();

    bool isAlive() const;
    bool isSelf() const;

    inline uint64_t pid() const {
#ifdef _WIN32
      return processId_;
#else
      return pid_;
#endif
    }

#ifdef _WIN32
    DWORD processId_;
#else
    pid_t pid_;
#endif
  };

  typedef boost::interprocess::allocator<Process, ManagedSHM::segment_manager>
      ProcessVectorAllocType;

  typedef boost::interprocess::vector<Process, ProcessVectorAllocType> ProcessVectorType;

  AuditorIPC(ManagedSHM::segment_manager* mgr) : processes(mgr) {}

  bool invalid = false;
  MutexIPC mutex;

  // Maintain a vector of processes using the pool
  // When this empties, the process should cleanup framework
  ProcessVectorType processes;
};

} // namespace cthulhu
