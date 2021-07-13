// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <memory>

#include <cthulhu/BufferTypes.h>
#include <cthulhu/ForceCleanable.h>
#include <cthulhu/LogDisabling.h>
#include <cthulhu/StreamInterface.h>

namespace cthulhu {

class MemoryPoolInterface : public ForceCleanable, public LogDisabling {
 public:
  virtual ~MemoryPoolInterface() = default;

  // Provides thread-safe access to the Sample Pool
  // A StreamID is provided, and the Framework transparently allocated a memory buffer from the
  // appropriate pool (local or shared) based on stream linkages with other processes
  virtual CpuBuffer getBufferFromPool(const StreamIDView& id, size_t nrBytes) = 0;

  // Equivalent to getBufferFromPool, but will request a GPU-backed buffer.
  virtual GpuBuffer getGpuBufferFromPool(size_t nrBytes, bool device_local) = 0;

  // Returns true if the provided pointer could have been returned as a buffer from this
  // memory pool.
  virtual bool isBufferFromPool(const AnyBuffer& buf) const = 0;

  // signal all connected processes that this section is no longer valid
  virtual void invalidate() = 0;

  // indicates whether this section is valid for use
  virtual bool isValid() const = 0;
};

} // namespace cthulhu
