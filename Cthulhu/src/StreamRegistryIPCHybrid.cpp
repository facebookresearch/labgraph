#include "StreamRegistryIPCHybrid.h"

#include <cthulhu/Framework.h>

#include <algorithm>
#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

#include <iostream>

namespace cthulhu {

StreamIPCHybrid::StreamIPCHybrid(
    const StreamDescription& desc,
    StreamInterfaceIPC* ipcStream,
    MemoryPoolIPCHybrid* memoryPool,
    size_t sampleParameterSize,
    size_t configParameterSize,
    size_t sampleDynamicFieldCount,
    size_t configDynamicFieldCount,
    ManagedSHM* shm)
    : StreamInterface(desc),
      ipcStream_(ipcStream),
      memoryPool_(memoryPool),
      ipcActive_(false),
      ipcProducer_(nullptr),
      ipcConsumer_(nullptr),
      sampleParameterSize_(sampleParameterSize),
      configParameterSize_(configParameterSize),
      sampleDynamicFieldCount_(sampleDynamicFieldCount),
      configDynamicFieldCount_(configDynamicFieldCount),
      shm_(shm) {}

StreamIPCHybrid::~StreamIPCHybrid() = default;

void StreamIPCHybrid::notifyMemoryPool() {
  if (!ipcStream_) {
    return;
  }
  if (ipcStream_->numSubscribers() > 0 && !ipcActive_) {
    // Notify the memory pool that it should be allocating this on
    // shared memory
    memoryPool_->activateStream(description_.id(), true);
    ipcActive_ = true;
  } else if (ipcStream_->numSubscribers() == 0 && ipcActive_) {
    memoryPool_->activateStream(description_.id(), false);
    ipcActive_ = false;
  }
}

bool StreamIPCHybrid::sendSample(const StreamSample& sample) {
  if (paused_) {
    return true;
  }

  std::unique_lock<std::timed_mutex> lock(timed_mutex_, std::defer_lock);
  if (!lock.try_lock_for(std::chrono::milliseconds(1))) {
    XR_LOGW("Failed to send sample--timed out.");
    return false;
  }

  for (const auto& consumer : consumers_) {
    consumer->consumeSample(sample);
  }
  sendSampleIPC(sample);

  return true;
}

void StreamIPCHybrid::sendSampleIPC(const StreamSample& sample) {
  if (!ipcProducer_) {
    return;
  }
  notifyMemoryPool();

  StreamSampleIPC ipcSample(shm_->get_segment_manager());

  bool lookupSuccess = false;

  switch (sample.payload.type) {
    case (BufferType::CPU): {
      auto result = memoryPool_->convert(std::get<CpuBuffer>(sample.payload.data));
      ipcSample.payload = result;
      ipcSample.payloadType = BufferType::CPU;
      lookupSuccess = result;
      break;
    }
    case (BufferType::GPU): {
      auto result = memoryPool_->convert(std::get<GpuBuffer>(sample.payload.data));
      ipcSample.payload = result;
      ipcSample.payloadType = BufferType::GPU;
      lookupSuccess = result;
      break;
    }
    default: {
      ipcSample.payloadType = BufferType::NULL_BUFFER;
      break;
    }
  }

  if (sample.payload && !lookupSuccess &&
      !Framework::instance().typeRegistry()->findTypeID(description_.type())->isBasic()) {
    if (ipcActive_) {
      XR_LOGW(
          "StreamIPCHybrid - Failed to lookup shared memory pointer for payload of stream '{}'",
          description_.id());
    }
    return;
  }
  ipcSample.timestamp = sample.metadata->header.timestamp;
  ipcSample.sequenceNumber = sample.metadata->header.sequenceNumber;
  ipcSample.numberOfSubSamples = sample.numberOfSubSamples;
  for (const auto& processingStamp : sample.metadata->processingStamps) {
    ProcessingStampKey key(shm_->get_segment_manager());
    key = processingStamp.first.c_str();
    ipcSample.processingStamps[key] = processingStamp.second;
  }
  if (sample.parameters) {
    auto sharedParametersPtr = memoryPool_->convert(sample.parameters);
    if (sharedParametersPtr) {
      ipcSample.parameters = sharedParametersPtr;
    } else {
      XR_LOGW_ONCE(
          "StreamIPCHybrid - Failed to lookup shared memory pointer when sending parameters of stream '{}'",
          description_.id());
      ipcSample.parameters = memoryPool_->getBufferFromSharedPoolDirect(sampleParameterSize_);
      memcpy(ipcSample.parameters.get().get(), sample.parameters.get(), sampleParameterSize_);
    }
  }

  if (sample.dynamicParameters) {
    ipcSample.dynamicSampleParameters =
        DynamicFields(sampleDynamicFieldCount_, shm_->get_segment_manager());
    for (size_t idx = 0; idx < ipcSample.dynamicSampleParameters.size(); ++idx) {
      auto& rawDynamicIPC = ipcSample.dynamicSampleParameters[idx];
      const auto& rawDynamic = *(sample.dynamicParameters.get() + idx);
      rawDynamicIPC.elementCount = rawDynamic.elementCount;
      rawDynamicIPC.elementSize = rawDynamic.elementSize;

      auto sharedDynamicParameterPtr = memoryPool_->convert(rawDynamic.raw);
      if (sharedDynamicParameterPtr) {
        rawDynamicIPC.raw = sharedDynamicParameterPtr;
      } else {
        XR_LOGW_ONCE(
            "StreamIPCHybrid - Failed to lookup shared memory pointer when sending dynamic parameter {} of stream '{}'",
            idx,
            description_.id());
        rawDynamicIPC.raw = memoryPool_->getBufferFromSharedPoolDirect(
            rawDynamicIPC.elementCount * rawDynamicIPC.elementSize);
        std::memcpy(
            rawDynamicIPC.raw.get().get(),
            rawDynamic.raw.get(),
            rawDynamicIPC.elementCount * rawDynamicIPC.elementSize);
      }
    }
  }
  ipcProducer_->publish(ipcSample);
}

bool StreamIPCHybrid::configure(const StreamConfig& config) {
  std::unique_lock<std::timed_mutex> lock(timed_mutex_, std::defer_lock);
  if (!lock.try_lock_for(std::chrono::milliseconds(1))) {
    XR_LOGW("Failed to configure stream--timed out.");
    return false;
  }

  configured_ = true;
  config_ = config;

  for (const auto& consumer : consumers_) {
    consumer->receiveConfig(config_);
  }
  configureIPC(config);
  return true;
}

void StreamIPCHybrid::configureIPC(const StreamConfig& config) {
  if (!ipcProducer_) {
    return;
  }
  notifyMemoryPool();
  StreamConfigIPC ipcConfig(shm_->get_segment_manager());
  ipcConfig.nominalSampleRate = config.nominalSampleRate;
  ipcConfig.sampleSizeInBytes = config.sampleSizeInBytes;
  ipcConfig.parameters = memoryPool_->getBufferFromSharedPoolDirect(configParameterSize_);
  memcpy(ipcConfig.parameters.get().get(), config.parameters.get(), configParameterSize_);

  if (config.dynamicParameters) {
    ipcConfig.dynamicConfigParameters =
        DynamicFields(configDynamicFieldCount_, shm_->get_segment_manager());
    for (size_t idx = 0; idx < ipcConfig.dynamicConfigParameters.size(); ++idx) {
      auto& rawDynamicIPC = ipcConfig.dynamicConfigParameters[idx];
      const auto& rawDynamic = *(config.dynamicParameters.get() + idx);
      rawDynamicIPC.elementCount = rawDynamic.elementCount;
      rawDynamicIPC.elementSize = rawDynamic.elementSize;
      rawDynamicIPC.raw = memoryPool_->getBufferFromSharedPoolDirect(
          rawDynamicIPC.elementCount * rawDynamicIPC.elementSize);
      std::memcpy(
          rawDynamicIPC.raw.get().get(),
          rawDynamic.raw.get(),
          rawDynamicIPC.elementCount * rawDynamicIPC.elementSize);
    }
  }

  ipcProducer_->configure(ipcConfig);
}

bool StreamIPCHybrid::receiveConfigIPC(const StreamConfigIPC& config) {
  StreamConfig local;
  local.nominalSampleRate = config.nominalSampleRate;
  local.sampleSizeInBytes = config.sampleSizeInBytes;
  local.parameters.reset(new uint8_t[configParameterSize_], [](uint8_t* p) -> void { delete[] p; });
  memcpy(local.parameters.get(), config.parameters.get().get(), configParameterSize_);

  if (!config.dynamicConfigParameters.empty()) {
    local.dynamicParameters = makeSharedRawDynamicArray(config.dynamicConfigParameters.size());
    for (size_t idx = 0; idx < config.dynamicConfigParameters.size(); ++idx) {
      auto& localRawDynamic = *(local.dynamicParameters.get() + idx);
      const auto& rawDynamicIPC = config.dynamicConfigParameters[idx];
      localRawDynamic.elementCount = rawDynamicIPC.elementCount;
      localRawDynamic.elementSize = rawDynamicIPC.elementSize;
      localRawDynamic.raw = std::shared_ptr<uint8_t>(
          new uint8_t[localRawDynamic.elementSize * localRawDynamic.elementCount](),
          std::default_delete<uint8_t[]>());
      std::memcpy(
          localRawDynamic.raw.get(),
          rawDynamicIPC.raw.get().get(),
          localRawDynamic.elementSize * localRawDynamic.elementCount);
    }
  }

  return configure(local);
}

bool StreamIPCHybrid::receiveSampleIPC(const StreamSampleIPC& sample) {
  StreamSample local;
  local.metadata.reset(new SampleMetadata());
  local.metadata->header.timestamp = sample.timestamp;
  local.metadata->header.sequenceNumber = sample.sequenceNumber;
  switch (sample.payloadType) {
    case (BufferType::CPU): {
      local.payload = memoryPool_->createLocal(std::get<SharedPtrIPC>(sample.payload));
      break;
    }
    case (BufferType::GPU): {
      local.payload = memoryPool_->createLocal(std::get<SharedPtrGPUIPC>(sample.payload));
      break;
    }
    default: {
      break;
    }
  }
  local.numberOfSubSamples = sample.numberOfSubSamples;
  for (const auto& processingStamp : sample.processingStamps) {
    std::string step(processingStamp.first.cbegin(), processingStamp.first.cend());
    local.metadata->processingStamps[step] = processingStamp.second;
  }
  if (sample.parameters) {
    auto sharedParametersPtr = memoryPool_->createLocal(sample.parameters);
    if (!sharedParametersPtr) {
      XR_LOGW(
          "StreamIPCHybrid - Failed to lookup shared memory pointer when receiving parameters of stream '{}'",
          description_.id());
      return false;
    }
    local.parameters = sharedParametersPtr;
  }

  if (!sample.dynamicSampleParameters.empty()) {
    local.dynamicParameters = makeSharedRawDynamicArray(sample.dynamicSampleParameters.size());
    for (size_t idx = 0; idx < sample.dynamicSampleParameters.size(); ++idx) {
      auto& localRawDynamic = *(local.dynamicParameters.get() + idx);
      const auto& rawDynamicIPC = sample.dynamicSampleParameters[idx];
      localRawDynamic.elementCount = rawDynamicIPC.elementCount;
      localRawDynamic.elementSize = rawDynamicIPC.elementSize;

      auto sharedDynamicParameterPtr = memoryPool_->createLocal(rawDynamicIPC.raw);
      if (sharedDynamicParameterPtr) {
        localRawDynamic.raw = sharedDynamicParameterPtr;
      } else {
        XR_LOGW(
            "StreamIPCHybrid - Failed to lookup shared memory pointer when receiving dynamic parameter {} of stream '{}'",
            idx,
            description_.id());
        return false;
      }
    }
  }
  return sendSample(local);
}

bool StreamIPCHybrid::hookProducer(const StreamProducer* const producer) {
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  if (producer_ != nullptr) {
    XR_LOGW("Not hooking producer on stream: {}", description_.id());
    return false;
  }
  XR_LOGD("Hooking producer on stream: {}", description_.id());
  producer_ = producer;
  if (ipcStream_) {
    ipcConsumer_.reset();
    ipcProducer_.reset(new StreamProducerIPC(ipcStream_));
  }

  return true;
}

void StreamIPCHybrid::hookConsumer(const StreamConsumer* const consumer) {
  XR_LOGD("Hooking consumer on stream: {}", description_.id());
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  consumers_.push_back(consumer);
  // If this is a basic stream, none of the downstream consumers are expecting to use
  // the config, but we still need to produce the signal
  bool isBasic = Framework::instance().typeRegistry()->findTypeID(description_.type())->isBasic();
  if (isConfigured() || isBasic) {
    consumer->receiveConfig(config_);
  }
  std::function<bool(const StreamConfigIPC&)> configCb = nullptr;
  if (ipcStream_) {
    if (!isBasic) {
      configCb = [this](const StreamConfigIPC& config) -> bool {
        return this->receiveConfigIPC(config);
      };
    }
    if (!producer_ && !ipcConsumer_) {
      ipcConsumer_.reset(new StreamConsumerIPC(
          ipcStream_, configCb, [this](const StreamSampleIPC& sample) -> bool {
            return this->receiveSampleIPC(sample);
          }));
    }
  }
}

void StreamIPCHybrid::removeProducer(const StreamProducer* const producer) {
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  if (producer_ == producer) {
    XR_LOGD("Removing producer on stream: {}", description_.id());
    producer_ = nullptr;
  } else {
    XR_LOGD("Not removing producer on stream: {}", description_.id());
    return;
  }
  ipcActive_ = false;

  if (ipcStream_) {
    ipcProducer_.reset();
    if (consumers_.size() > 0) {
      std::function<bool(const StreamConfigIPC&)> configCb = nullptr;
      if (!Framework::instance().typeRegistry()->findTypeID(description_.type())->isBasic()) {
        configCb = [this](const StreamConfigIPC& config) -> bool {
          return this->receiveConfigIPC(config);
        };
      }

      ipcConsumer_.reset(new StreamConsumerIPC(
          ipcStream_,
          configCb,
          [this](const StreamSampleIPC& sample) -> bool { return this->receiveSampleIPC(sample); },
          false));
    }
  }
}

void StreamIPCHybrid::removeConsumer(const StreamConsumer* const consumer) {
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);

  auto it = std::find(consumers_.begin(), consumers_.end(), consumer);
  if (it != consumers_.end()) {
    XR_LOGD("Removing consumer on stream: {}", description_.id());
    consumers_.erase(it);
  }
  if (ipcStream_) {
    if (ipcConsumer_ && consumers_.empty()) {
      ipcConsumer_.reset();
    }
  }
}

StreamRegistryIPCHybrid::StreamRegistryIPCHybrid(
    MemoryPoolIPCHybrid* memoryPool,
    const TypeRegistryInterface* typeRegistry,
    ManagedSHM* shm)
    : shm_(shm), memoryPool_(memoryPool), typeRegistry_(typeRegistry) {
  registryData_ =
      shm_->find_or_construct<StreamRegistryIPC>("StreamRegistry")(shm_->get_segment_manager());

  if (registryData_ == nullptr) {
    auto str = "Failed to open stream registry in shared memory.";
    XR_LOGE("{}", str);
    throw std::runtime_error(str);
  }
  // This poses a risk to nuke. If it is locked by a dead process, we will hang
  ScopedLockIPC lock(registryData_->registry_lock);
  // even after ignoring this lock, we can still hang, presumably due to another lock
  registryData_->reference_count++;
}

bool StreamRegistryIPCHybrid::nuke(ManagedSHM* shm) {
  shm->destroy<StreamRegistryIPC>("StreamRegistry");
  return true;
}

StreamRegistryIPCHybrid::~StreamRegistryIPCHybrid() {
  {
    const auto lock = std::lock_guard(streamMutex_);
    streams_.clear();
  }

  if (registryData_) {
    ScopedLockIPC lock(registryData_->registry_lock);
    registryData_->reference_count--;
    if (registryData_->reference_count == 0 || force_clean_) {
      registryData_->streams.clear();
      registryData_->reference_count = 0;
      if (log_enabled_) {
        XR_LOGD("Cleaning up ipc stream registry.");
      }
    } else if (log_enabled_) {
      XR_LOGD(
          "Not cleaning ipc stream registry, still references: {}", registryData_->reference_count);
    }
  }
}

StreamInterface* StreamRegistryIPCHybrid::registerStream(const StreamDescription& desc) {
  std::lock_guard<std::mutex> lock(streamMutex_);

  auto type = typeRegistry_->findTypeID(desc.type());

  // Lookup type name in registry
  StreamDescriptionIPC descIPC(shm_->get_segment_manager());
  descIPC.id = desc.id().c_str();
  descIPC.type = type->typeName().c_str();

  // Go to the shared memory first
  StreamInterfaceIPC* ipcStream = nullptr;
  {
    StreamIDIPC idIPC(shm_->get_segment_manager());
    idIPC = desc.id().c_str();
    ScopedLockIPC ipcLock(registryData_->registry_lock);
    if (registryData_->streams.find(idIPC) == registryData_->streams.end()) {
      registryData_->streams.try_emplace(idIPC, descIPC);
    }
    ipcStream = &(registryData_->streams.at(idIPC));
  }

  // Then go to local
  auto s = streams_.find(desc.id());
  if (s != streams_.end()) {
    return static_cast<StreamInterface*>(&(s->second));
  }

  size_t sampleSize = type->sampleParameterSize();
  size_t configSize = type->configParameterSize();
  size_t sampleDynamicFieldCount = type->sampleNumberDynamicFields();
  size_t configDynamicFieldCount = type->configNumberDynamicFields();

  // Create hybrid in local if it doesn't exist
  XR_LOGD("Inserting stream: {} into local registry.", desc.id());
  streams_.insert(std::make_pair(
      desc.id(),
      StreamIPCHybrid(
          desc,
          ipcStream,
          memoryPool_,
          sampleSize,
          configSize,
          sampleDynamicFieldCount,
          configDynamicFieldCount,
          shm_)));
  return static_cast<StreamInterface*>(&(streams_.find(desc.id())->second));
}

StreamInterface* StreamRegistryIPCHybrid::getStream(const StreamID& id) {
  std::lock_guard<std::mutex> lock(streamMutex_);

  // Go to the shared memory first
  StreamInterfaceIPC* ipcStream = nullptr;
  {
    StreamIDIPC idIPC(shm_->get_segment_manager());
    idIPC = id.c_str();
    ScopedLockIPC ipcLock(registryData_->registry_lock);
    if (registryData_->streams.find(idIPC) == registryData_->streams.end()) {
      XR_LOGD(
          "Requested a stream '{}' from the registry that does not exist, "
          "and insertion is not allowed.",
          id);
      return nullptr;
    }
    ipcStream = &(registryData_->streams.at(idIPC));
  }

  // Then go to local
  auto s = streams_.find(id);
  if (s != streams_.end()) {
    return static_cast<StreamInterface*>(&(s->second));
  }

  if (!ipcStream) {
    return nullptr;
  }

  // If its in IPC, we're allowed to bring it to local. Just need to lookup the type
  auto type = typeRegistry_->findTypeName(ipcStream->description().type.c_str());
  StreamDescription desc{id, type->typeID()};

  size_t sampleSize = type->sampleParameterSize();
  size_t configSize = type->configParameterSize();
  size_t sampleDynamicFieldCount = type->sampleNumberDynamicFields();
  size_t configDynamicFieldCount = type->configNumberDynamicFields();

  // Create hybrid in local if it doesn't exist
  XR_LOGD("Inserting stream: {} into local registry.", desc.id());
  streams_.insert(std::make_pair(
      desc.id(),
      StreamIPCHybrid(
          desc,
          ipcStream,
          memoryPool_,
          sampleSize,
          configSize,
          sampleDynamicFieldCount,
          configDynamicFieldCount,
          shm_)));
  return static_cast<StreamInterface*>(&(streams_.find(desc.id())->second));
}

void StreamRegistryIPCHybrid::printStreamInfo() const {
  std::lock_guard<std::mutex> lock(streamMutex_);
  std::cout << "There are " << streams_.size() << " streams in the registry.\n";
  for (const auto& stream : streams_) {
    std::cout << stream.first << ":"
              << "\n";
    std::cout << "\tProducer: " << (stream.second.producer() == nullptr ? "OFF" : "ON") << "\n";
    std::cout << "\tConsumers: " << stream.second.consumers().size() << "\n";
  }
  std::cout << std::flush;
};

std::vector<StreamID> StreamRegistryIPCHybrid::streamsOfTypeID(uint32_t typeID) const {
  std::vector<StreamID> ids;

  if (typeID == 0) {
    return ids;
  }

  // Lookup type name in registry
  std::string type = typeRegistry_->findTypeID(typeID)->typeName();

  // No point in checking local, the set of all streams are in ipc
  ScopedLockIPC lock2(registryData_->registry_lock);
  for (auto& stream : registryData_->streams) {
    if (stream.second.description().type.c_str() == type) {
      ids.push_back(stream.first.c_str());
    }
  }

  return ids;
};

} // namespace cthulhu
