// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include "StreamInterfaceIPC.h"

#include <boost/interprocess/containers/map.hpp>
#include <boost/interprocess/containers/string.hpp>

#include <unordered_map>

namespace cthulhu {

struct StreamRegistryIPC {
  typedef boost::interprocess::
      allocator<std::pair<const StreamIDIPC, StreamInterfaceIPC>, ManagedSHM::segment_manager>
          MapAllocType;
  typedef boost::interprocess::
      map<StreamIDIPC, StreamInterfaceIPC, std::less<StreamIDIPC>, MapAllocType>
          MapType;

  StreamRegistryIPC() = delete;
  StreamRegistryIPC(const StreamRegistryIPC&) = delete;
  StreamRegistryIPC(StreamRegistryIPC&&) = delete;

  StreamRegistryIPC(const MapAllocType& alloc) : streams(std::less<StreamIDIPC>(), alloc) {}

  MapType streams;
  MutexIPC registry_lock;

  // Maintain a count of processes using the registry.
  // When this reaches 0, the process should cleanup the map
  uint32_t reference_count = 0;
};

} // namespace cthulhu
