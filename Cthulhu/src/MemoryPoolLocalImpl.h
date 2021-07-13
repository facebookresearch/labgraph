// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <atomic>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <vector>

namespace cthulhu {

class MemoryPool {
  using ByteType = uint8_t;

  struct Reclaimer {
    //! Construct a buffer reclaimer for the specified buffer pool host.
    Reclaimer(MemoryPool* _host, const std::shared_ptr<void>& _sentinel);
    //! The method to be invoked to reclaim the buffer.
    void operator()(void* ptr) const;

   protected:
    MemoryPool* host; //!< A pointer to the host that this reclaimer is servicing.
    std::weak_ptr<void>
        sentinel; //!< The expiration of this sentinel indicates the deconstruction of the host.
  };

 public:
  static constexpr size_t ALLOCATED_MAX_BYTES = 1 << 30;
  MemoryPool(size_t allocatedMax = ALLOCATED_MAX_BYTES);
  virtual ~MemoryPool();

  //! Request a memory area of the specified size from the memory pool.
  std::shared_ptr<ByteType> request(size_t nrBytes);

  //! Release all the memory areas that are allocated but not currently used.
  size_t shrink();

  //! Retrieve the number of bytes that the current memory pool occupies.
  size_t bytesAllocated() const;

 private:
  friend struct Reclaimer;
  //! Reclaim a memory area back to the memory pool.
  void reclaim(void* ptr);

  std::atomic<size_t> allocated_;
  std::atomic<size_t> allocatedMax_;
  std::mutex storeMutex_, sizesMutex_;
  std::unordered_map<uintptr_t, size_t> sizes_;
  std::unordered_map<size_t, std::vector<void*>> store_;
  std::shared_ptr<void> sentinel_;
  // The reclaimer maintains a weak reference to this sentinel. The deletion
  // of this sentinel will result in the reclaimer to be alerted, and not
  // invoke the reclaim method in this instance anymore.
};

} // namespace cthulhu
