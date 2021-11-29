#include "ContextRegistryIPC.h"
#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

std::string ContextInfoIPCHandle::name() const {
  return std::string(data_->name_.data(), data_->name_.size());
}

bool ContextInfoIPCHandle::isPrivateNamespace() const {
  return data_->private_ns_;
}

int ContextInfoIPCHandle::getPid() const {
  return data_->pid_;
}

bool ContextInfoIPCHandle::getValid() const {
  return data_->valid_.load(std::memory_order_acquire);
}

void ContextInfoIPCHandle::setValid(bool valid) {
  data_->valid_.store(valid, std::memory_order_release);
}

std::vector<ContextInfoInterface::RegistrationGroup> ContextInfoIPCHandle::subscriptions() const {
  ScopedLockIPC lock(data_->mutex);

  std::vector<ContextInfoInterface::RegistrationGroup> out_subs;
  out_subs.reserve(data_->subscriptions_.size());
  for (const auto& sub : data_->subscriptions_) {
    auto& out_sub = out_subs.emplace_back();
    out_sub.reserve(sub.size());
    for (const auto& s : sub) {
      out_sub.emplace_back(s.c_str());
    }
  }

  return out_subs;
}

std::vector<ContextInfoInterface::RegistrationGroup> ContextInfoIPCHandle::publications() const {
  ScopedLockIPC lock(data_->mutex);

  std::vector<ContextInfoInterface::RegistrationGroup> out_pubs;
  out_pubs.reserve(data_->publications_.size());
  for (const auto& pub : data_->publications_) {
    auto& out_pub = out_pubs.emplace_back();
    out_pub.reserve(pub.size());
    for (const auto& p : pub) {
      out_pub.emplace_back(p.c_str());
    }
  }

  return out_pubs;
}

std::vector<
    std::pair<ContextInfoInterface::RegistrationGroup, ContextInfoInterface::RegistrationGroup>>
ContextInfoIPCHandle::transformations() const {
  ScopedLockIPC lock(data_->mutex);
  std::vector<
      std::pair<ContextInfoInterface::RegistrationGroup, ContextInfoInterface::RegistrationGroup>>
      out_tfs;
  out_tfs.reserve(data_->transformations_.size());

  for (const auto& [inputs, outputs] : data_->transformations_) {
    auto& [out_inputs, out_outputs] = out_tfs.emplace_back();
    out_inputs.reserve(inputs.size());
    out_outputs.reserve(outputs.size());
    for (const auto& input : inputs) {
      out_inputs.emplace_back(input.c_str());
    }
    for (const auto& output : outputs) {
      out_outputs.emplace_back(output.c_str());
    }
  }

  return out_tfs;
}

void ContextInfoIPCHandle::registerSubscriber(const std::vector<StreamID>& streams) {
  ScopedLockIPC lock(data_->mutex);
  auto& back = data_->subscriptions_.emplace_back(alloc_);
  for (const auto& stream : streams) {
    back.emplace_back(stream.c_str(), alloc_);
  }
}

void ContextInfoIPCHandle::registerPublisher(const std::vector<StreamID>& streams) {
  ScopedLockIPC lock(data_->mutex);
  auto& back = data_->publications_.emplace_back(alloc_);
  for (const auto& stream : streams) {
    back.emplace_back(stream.c_str(), alloc_);
  }
}

void ContextInfoIPCHandle::registerTransformer(
    const std::vector<StreamID>& inputs,
    const std::vector<StreamID>& outputs) {
  ScopedLockIPC lock(data_->mutex);
  auto& [first, second] = data_->transformations_.emplace_back(alloc_, alloc_);
  for (const auto& input : inputs) {
    first.emplace_back(input.c_str(), alloc_);
  }

  for (const auto& output : outputs) {
    second.emplace_back(output.c_str(), alloc_);
  }
}

void ContextInfoIPCHandle::registerSubscriber(const std::vector<StreamIDView>& views) {
  ScopedLockIPC lock(data_->mutex);
  auto& back = data_->subscriptions_.emplace_back(alloc_);
  for (const auto& view : views) {
    back.emplace_back(view.data(), alloc_);
  }
}

void ContextInfoIPCHandle::registerPublisher(const std::vector<StreamIDView>& views) {
  ScopedLockIPC lock(data_->mutex);
  auto& back = data_->publications_.emplace_back(alloc_);
  for (const auto& view : views) {
    back.emplace_back(view.data(), alloc_);
  }
}

void ContextInfoIPCHandle::registerTransformer(
    const std::vector<StreamIDView>& input_views,
    const std::vector<StreamIDView>& output_views) {
  ScopedLockIPC lock(data_->mutex);
  auto& [first, second] = data_->transformations_.emplace_back(alloc_, alloc_);
  for (const auto& input : input_views) {
    first.emplace_back(input.data(), alloc_);
  }

  for (const auto& output : output_views) {
    second.emplace_back(output.data(), alloc_);
  }
}

ContextRegistryIPC::ContextRegistryIPC(ManagedSHM* shm) : shm_(shm) {
  registryData_ = shm_->find_or_construct<ContextRegistryIPCData>("ContextRegistry")(
      shm_->get_segment_manager());

  if (registryData_ == nullptr) {
    const auto str = "Failed to open context registry in shared memory.";
    XR_LOGE("{}", str);
    throw std::runtime_error(str);
  }

  ScopedLockIPC lock(registryData_->mutex);
  registryData_->referenceCount++;
  XR_LOGD("reference count is now {}", registryData_->referenceCount);
}

bool ContextRegistryIPC::nuke(ManagedSHM* shm) {
  shm->destroy<ContextRegistryIPCData>("ContextRegistry");
  return true;
}

ContextRegistryIPC::~ContextRegistryIPC() {
  if (registryData_) {
    ScopedLockIPC lock(registryData_->mutex);
    registryData_->referenceCount--;
    if (registryData_->referenceCount == 0 || force_clean_) {
      registryData_->referenceCount = 0;
      registryData_->contexts.clear();
      if (log_enabled_) {
        XR_LOGD("Cleaning up ipc context registry.");
      }
    } else {
      if (log_enabled_) {
        XR_LOGD(
            "Not cleaning ipc context registry, still references: {}",
            registryData_->referenceCount);
      }
    }
  }
}

ContextInfoInterface* ContextRegistryIPC::registerContext(std::string_view name, bool private_ns) {
  ScopedLockIPC lock(registryData_->mutex);

  auto& back = registryData_->contexts.emplace_back(name, private_ns, shm_->get_segment_manager());
  ++registryData_->valid_contexts; // Need to track valid size separately to avoid looping.
  XR_LOGD(
      "adding context {}, {}, up to {} valid contexts out of {}",
      std::string(name),
      static_cast<const void*>(&back),
      registryData_->valid_contexts,
      registryData_->contexts.size());

  auto& handle = handles_.emplace_back(&back, shm_->get_segment_manager());
  return &handle;
}

void ContextRegistryIPC::removeContext(ContextInfoInterface* handle) {
  auto* ipc_handle = static_cast<ContextInfoIPCHandle*>(handle);
  ScopedLockIPC lock(registryData_->mutex);

  bool matched = false;
  for (auto& ctx : registryData_->contexts) {
    if (&ctx == ipc_handle->data_) {
      ipc_handle->setValid(false); // Use the convenient handle we've been given
      --registryData_->valid_contexts;
      matched = true;
    }
  }
  if (!matched) {
    XR_LOGE("no match found for context {}", static_cast<const void*>(ipc_handle->data_));
    return;
  }

  XR_LOGD(
      "removed context {} ({}), down to {} valid contexts out of {}",
      ipc_handle->name(),
      static_cast<const void*>(ipc_handle->data_),
      registryData_->valid_contexts,
      registryData_->contexts.size());

  // Rather than removing the context, as below, we simply mark the context as invalid. This keeps
  // slightly more contexts stored in memory, but has the advantage of being able to handle badly
  // behaving programs which don't keep contexts around permanently. Uncomment the following lines
  // to completely remove the context instead.
  // registryData_->contexts.remove_if([ipc_handle](auto& ctx) {
  //   return &ctx == ipc_handle->data_;
  // });
  ipc_handle->data_ = nullptr; // Null the handle just in case someone decides to use it again
}

// Identical implementation to allContexts(), but only returns valid contexts instead of all.
std::vector<ContextInfoInterfaceConstPtr> ContextRegistryIPC::contexts(bool all) const {
  ScopedLockIPC lock(registryData_->mutex);

  std::vector<ContextInfoInterfaceConstPtr> out;
  out.reserve(registryData_->contexts.size());
  for (auto& ctx : registryData_->contexts) {
    if (all || ctx.valid_) {
      out.emplace_back(new ContextInfoIPCHandle(&ctx, shm_->get_segment_manager()));
    }
  }

  return out;
}

} // namespace cthulhu
