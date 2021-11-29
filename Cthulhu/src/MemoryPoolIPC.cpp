#include "MemoryPoolIPC.h"

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

#ifndef _WIN32
#include <signal.h>
#endif

namespace cthulhu {

void ReclaimerIPC::operator()(const pointer& p) {
  host->reclaim(offset);
}

void MemoryPoolIPC::reclaim(std::ptrdiff_t off) {
  size_t size = 0;
  {
    ScopedLockIPC lock(sizes_mutex);
    const auto it = sizes.find(off);
    if (it != sizes.cend())
      size = it->second;
  }
  {
    ScopedLockIPC lock(buffers_mutex);
    auto it = buffers.find(size);
    if (it != buffers.end()) {
      it->second.push_back(off);
    }
  }
}

void ReclaimerGPUIPC::operator()(const pointer& p) {
  host->reclaim(offset);
}

} // namespace cthulhu
