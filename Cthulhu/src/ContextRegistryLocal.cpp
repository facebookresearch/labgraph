#include "ContextRegistryLocal.h"

#include <algorithm>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

ContextInfoInterface* ContextRegistryLocal::registerContext(
    std::string_view name,
    bool private_ns) {
  // Return a raw pointer to the ContextInfoLocal. This is acceptable as the context info will be
  // in scope for the lifetime of the Context. Doesn't matter if there's duplicates.
  return contexts_.emplace_back(new ContextInfoLocal(name, private_ns)).get();
}

void ContextRegistryLocal::removeContext(ContextInfoInterface* handle) {
  auto it = std::remove_if(
      contexts_.begin(), contexts_.end(), [handle](auto& p) { return p.get() == handle; });

  if (it == contexts_.end()) { // no elems removed
    XR_LOGE("no elements removed");
    throw std::runtime_error("no elements removed");
  }
  contexts_.erase(it, contexts_.end());
}

std::vector<ContextInfoInterfaceConstPtr> ContextRegistryLocal::contexts(
    bool /* all unused */) const {
  std::vector<ContextInfoInterfaceConstPtr> ret;
  ret.reserve(contexts_.size());
  for (const auto& ctx : contexts_) {
    // Copy construct the context info and store it in a new pointer
    ret.emplace_back(new ContextInfoLocal(*ctx));
  }
  return ret;
}

} // namespace cthulhu
