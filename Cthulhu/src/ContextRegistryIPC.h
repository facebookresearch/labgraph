// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include "IPCEssentials.h"

#include <boost/interprocess/containers/list.hpp>
#include <boost/interprocess/containers/vector.hpp>
#include <boost/interprocess/sync/interprocess_mutex.hpp>
#include <cthulhu/ContextRegistryInterface.h>

#include <atomic>
#include <list>

namespace cthulhu {

using SegmentManager = ManagedSHM::segment_manager;
using VoidAllocatorIPC = boost::interprocess::allocator<void, SegmentManager>;

using StreamIDIPCAllocator = boost::interprocess::allocator<StreamIDIPC, SegmentManager>;
using VectorStreamIDIPC = boost::interprocess::vector<StreamIDIPC, StreamIDIPCAllocator>;
using VectorStreamIDIPCAllocator =
    boost::interprocess::allocator<VectorStreamIDIPC, SegmentManager>;
using VectorVectorStreamIDIPC =
    boost::interprocess::vector<VectorStreamIDIPC, VectorStreamIDIPCAllocator>;

using PairVectorVectorStreamIDIPC = std::pair<VectorStreamIDIPC, VectorStreamIDIPC>;
using PairVectorVectorStreamIDIPCAllocator =
    boost::interprocess::allocator<PairVectorVectorStreamIDIPC, SegmentManager>;
using VectorPairVectorVectorStreamIDIPC =
    boost::interprocess::vector<PairVectorVectorStreamIDIPC, PairVectorVectorStreamIDIPCAllocator>;

// Forward declare to use as friend in ContextInfoIPCHandle
class ContextRegistryIPC;

struct ContextInfoIPCData {
  StreamIDIPC name_;
  bool private_ns_;
  // PID is tracked to be able to differentiate between processes. There should be some more
  // sophistication somewhere which allows the determination of IPC vs threading, but that may not
  // belong here.
  int pid_;

  // Store whether the IPC data is still valid. In some cases, Contexts are treated as ephemeral,
  // which will normally remove the data from the registry. This is good default behavior, and what
  // we want to tend towards, but keeping the data around so it's possible to either see history, or
  // see what broken nodes have done, is important.
  static_assert(std::atomic_bool::is_always_lock_free, "bool must be lock free!");
  std::atomic_bool valid_;

  mutable MutexIPC mutex;
  VectorVectorStreamIDIPC publications_;
  VectorVectorStreamIDIPC subscriptions_;
  VectorPairVectorVectorStreamIDIPC transformations_;

  ContextInfoIPCData(std::string_view name, bool private_ns, const VoidAllocatorIPC& alloc)
      : name_(name.data(), name.size(), alloc),
        private_ns_(private_ns),
        pid_(boost::interprocess::ipcdetail::get_current_process_id()),
        valid_(true),
        publications_(alloc),
        subscriptions_(alloc),
        transformations_(alloc) {}
};

class ContextInfoIPCHandle : public ContextInfoInterface {
 public:
  ContextInfoIPCHandle(ContextInfoIPCData* data, const VoidAllocatorIPC& alloc)
      : data_(data), alloc_(alloc) {}
  virtual ~ContextInfoIPCHandle() = default;

  std::string name() const override;
  bool isPrivateNamespace() const override;
  int getPid() const override;
  bool getValid() const override;
  void setValid(bool valid);

  std::vector<RegistrationGroup> subscriptions() const override;
  std::vector<RegistrationGroup> publications() const override;
  std::vector<std::pair<RegistrationGroup, RegistrationGroup>> transformations() const override;

  void registerSubscriber(const std::vector<StreamID>& streams) override;
  void registerPublisher(const std::vector<StreamID>& streams) override;
  void registerTransformer(
      const std::vector<StreamID>& inputs,
      const std::vector<StreamID>& outputs) override;

  void registerSubscriber(const std::vector<StreamIDView>& views) override;
  void registerPublisher(const std::vector<StreamIDView>& views) override;
  void registerTransformer(
      const std::vector<StreamIDView>& input_views,
      const std::vector<StreamIDView>& output_views) override;

 private:
  ContextInfoIPCData* data_;
  VoidAllocatorIPC alloc_;

  friend class ContextRegistryIPC;
};

using ContextInfoAllocType =
    boost::interprocess::allocator<ContextInfoIPCData, ManagedSHM::segment_manager>;
using ContextInfoList = boost::interprocess::list<ContextInfoIPCData, ContextInfoAllocType>;

struct ContextRegistryIPCData {
  MutexIPC mutex;
  ContextInfoList contexts;
  size_t valid_contexts = 0;

  // Must only be updated with mutex held
  uint32_t referenceCount = 0;

  ContextRegistryIPCData(const VoidAllocatorIPC& alloc) : contexts(alloc) {}
};

class ContextRegistryIPC : public ContextRegistryInterface {
 public:
  ContextRegistryIPC(ManagedSHM* shm);
  virtual ~ContextRegistryIPC();

  ContextInfoInterface* registerContext(std::string_view name, bool private_ns = false) override;
  void removeContext(ContextInfoInterface* handle) override;
  std::vector<ContextInfoInterfaceConstPtr> contexts(bool all = false) const override;

  // Destroy the framework without any concern for other Cthulhu users
  //
  // Intended to be used as last-resort cleanup of a misbehaving Cthulhu framework.
  // Users should typically favor cleanup().
  static bool nuke(ManagedSHM* shm);

 private:
  ContextRegistryIPCData* registryData_ = nullptr;
  std::list<ContextInfoIPCHandle> handles_; // These are the handles we've issued
  ManagedSHM* shm_;
};
} // namespace cthulhu
