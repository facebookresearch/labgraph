#include "MemoryPoolLocalImpl.h"

namespace cthulhu {

MemoryPool::Reclaimer::Reclaimer(MemoryPool* _host, const std::shared_ptr<void>& _sentinel)
    : host(_host), sentinel(_sentinel) {}

void MemoryPool::Reclaimer::operator()(void* ptr) const {
  // sentinel.expired would return true if the shared_ptr out of which this weak_ptr
  // is constructed has been deleted. This call is guaranteed to be thread-safe by the
  // standard. The deconstruction of the sentinel in the buffer pool instance takes
  // place before any other book-keeping entities are deleted. In case of expiration,
  // we simply call operator delete[]; otherwise, we request the host to reclaim.

  if (sentinel.expired()) {
    delete[] static_cast<char*>(ptr);
  } else {
    host->reclaim(ptr);
  }
}

std::shared_ptr<MemoryPool::ByteType> MemoryPool::request(size_t nrBytes) {
  void* ptr = nullptr;

  {
    // First of all, we look into the existent pool of buffers of the requested size
    // to see if there is anything directly usable; if false, a container of pointers
    // is created. In either case, we attempt to pull one of those allocated buffers
    // from the pool (which automatically fails if it is just created).

    std::lock_guard<std::mutex> lock(storeMutex_);
    auto store_it = store_.find(nrBytes);
    if (store_it == store_.end()) {
      store_it =
          store_
              .emplace(
                  std::piecewise_construct, std::forward_as_tuple(nrBytes), std::forward_as_tuple())
              .first;
    }

    auto& ptrlist = store_it->second;
    if (!ptrlist.empty()) {
      ptr = ptrlist.back();
      ptrlist.pop_back();
    }
  }

  // Now, if ptr is still null, we would need to allocate some new space for it.
  // This should only happen if the FIFO is not being dequeued promptly. We check
  // to see if allocating more space to lead to exceeding the byte limitation,
  // and attempt to shrink the buffer pool if necessary. An attempt is then made
  // to invoke operator new to get some space from the system, and the size lookup
  // table is updated accordingly.

  if (!ptr) {
    if (allocated_ + nrBytes > allocatedMax_)
      shrink();
    if (allocated_ + nrBytes <= allocatedMax_) {
      if ((ptr = new (std::nothrow) MemoryPool::ByteType[nrBytes]{0})) {
        allocated_ += nrBytes;
        {
          std::lock_guard<std::mutex> lock(sizesMutex_);
          sizes_.emplace(reinterpret_cast<uintptr_t>(ptr), nrBytes);
        }
      }
    }
  }

  return std::shared_ptr<ByteType>(static_cast<ByteType*>(ptr), Reclaimer(this, sentinel_));
}

void MemoryPool::reclaim(void* ptr) {
  // This method is called from the reclaimer to recycle the pointer
  // (and its associated memory space, of course) to the memory pool.
  // No action is taken if this pointer is not allocated by this pool.

  size_t size = 0;
  {
    std::lock_guard<std::mutex> lock(sizesMutex_);
    const auto it = sizes_.find(reinterpret_cast<uintptr_t>(ptr));
    if (it != sizes_.cend())
      size = it->second;
  }
  {
    std::lock_guard<std::mutex> lock(storeMutex_);
    store_[size].push_back(ptr);
  }
}

size_t MemoryPool::shrink() {
  size_t shrinked = 0;
  decltype(store_) empty;
  {
    std::lock_guard<std::mutex> lock(storeMutex_);
    store_.swap(empty);
  }

  // To avoid holding the mutex for an excessive amount of time, we first swap
  // the content of the memory pool with some local container; this means that
  // any operation on the previous memory pool will be on the local object that
  // is not subject to thread-safety considerations. Also, a list of memory areas
  // to be deallocated is maintained for deferred maintenance of the size table.

  std::vector<uintptr_t> to_deallocate;
  for (auto& pair : empty) {
    for (auto& ptr : pair.second) {
      to_deallocate.push_back(reinterpret_cast<uintptr_t>(ptr));
      delete[] static_cast<MemoryPool::ByteType*>(ptr);

      allocated_ -= pair.first;
      shrinked += pair.first;
    }
  }

  {
    std::lock_guard<std::mutex> lock(sizesMutex_);
    for (const auto& address : to_deallocate)
      sizes_.erase(address);
  }

  return shrinked;
}

size_t MemoryPool::bytesAllocated() const {
  return allocated_;
}

MemoryPool::~MemoryPool() {
  shrink();
}

MemoryPool::MemoryPool(size_t allocatedMax)
    : allocated_(0), allocatedMax_(allocatedMax), sentinel_(new size_t) {}

} // namespace cthulhu
