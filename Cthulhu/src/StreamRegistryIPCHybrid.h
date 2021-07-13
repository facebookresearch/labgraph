// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <map>
#include <mutex>

#include "MemoryPoolIPCHybrid.h"
#include "StreamRegistryIPC.h"

#include <cthulhu/StreamRegistryInterface.h>
#include <cthulhu/TypeRegistryInterface.h>

namespace cthulhu {

class StreamIPCHybrid : public StreamInterface {
 public:
  StreamIPCHybrid(
      const StreamDescription& desc,
      StreamInterfaceIPC* ipcStream,
      MemoryPoolIPCHybrid* memoryPool,
      size_t sampleParameterSize,
      size_t configParameterSize,
      size_t sampleDynamicFieldCount,
      size_t configDynamicFieldCount,
      ManagedSHM*);
  virtual ~StreamIPCHybrid();

  // Non-copyable. Only one should exist, sitting in the Registry
  StreamIPCHybrid(const StreamIPCHybrid& other) = delete;
  StreamIPCHybrid& operator=(const StreamIPCHybrid& other) = delete;

  // Move-constructable, only for insertion into the Registry
  StreamIPCHybrid(StreamIPCHybrid&& other)
      : StreamInterface(std::move(other)),
        ipcStream_(other.ipcStream_),
        memoryPool_(other.memoryPool_),
        ipcActive_(other.ipcActive_),
        ipcProducer_(std::move(other.ipcProducer_)),
        ipcConsumer_(std::move(other.ipcConsumer_)),
        sampleParameterSize_(other.sampleParameterSize_),
        configParameterSize_(other.configParameterSize_),
        sampleDynamicFieldCount_(other.sampleDynamicFieldCount_),
        configDynamicFieldCount_(other.configDynamicFieldCount_),
        shm_(other.shm_) {}
  // Non move assignable, shouldn't be needed
  StreamIPCHybrid& operator=(StreamIPCHybrid&& other) = delete;

 protected:
  virtual bool sendSample(const StreamSample& sample) override;

  virtual bool configure(const StreamConfig& config) override;

  virtual bool hookProducer(const StreamProducer* const producer) override;

  virtual void hookConsumer(const StreamConsumer* const consumer) override;

  virtual void removeProducer(const StreamProducer* const producer) override;

  virtual void removeConsumer(const StreamConsumer* const consumer) override;

 private:
  void notifyMemoryPool();
  void sendSampleIPC(const StreamSample& sample);
  void configureIPC(const StreamConfig& config);
  bool receiveConfigIPC(const StreamConfigIPC& config);
  bool receiveSampleIPC(const StreamSampleIPC& sampleData);

  StreamInterfaceIPC* ipcStream_;
  MemoryPoolIPCHybrid* memoryPool_;

  bool ipcActive_;

  std::unique_ptr<StreamProducerIPC> ipcProducer_;
  std::unique_ptr<StreamConsumerIPC> ipcConsumer_;

  size_t sampleParameterSize_;
  size_t configParameterSize_;
  size_t sampleDynamicFieldCount_;
  size_t configDynamicFieldCount_;
  ManagedSHM* shm_;
};

class StreamRegistryIPCHybrid : public StreamRegistryInterface {
 public:
  StreamRegistryIPCHybrid(
      MemoryPoolIPCHybrid* memoryPool,
      const TypeRegistryInterface* typeRegistry,
      ManagedSHM* shm);
  virtual ~StreamRegistryIPCHybrid();

  virtual StreamInterface* registerStream(const StreamDescription& desc) override;

  virtual StreamInterface* getStream(const StreamID& id) override;

  virtual void printStreamInfo() const override;

  virtual std::vector<StreamID> streamsOfTypeID(uint32_t typeID) const override;

  // Destroy the framework without any concern for other Cthulhu users
  //
  // Intended to be used as last-resort cleanup of a misbehaving Cthulhu framework.
  // Users should typically favor cleanup().
  static bool nuke(ManagedSHM* shm);

 private:
  std::map<const StreamID, StreamIPCHybrid> streams_;
  mutable std::mutex streamMutex_;
  StreamRegistryIPC* registryData_ = nullptr;

  ManagedSHM* shm_;
  MemoryPoolIPCHybrid* memoryPool_;
  const TypeRegistryInterface* typeRegistry_;
};

} // namespace cthulhu
