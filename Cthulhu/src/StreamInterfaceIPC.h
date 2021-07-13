// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/StreamInterface.h>
#include "IPCEssentials.h"

#include <boost/interprocess/containers/list.hpp>
#include <boost/interprocess/containers/map.hpp>
#include <boost/interprocess/containers/string.hpp>
#include <boost/interprocess/containers/vector.hpp>
#include <boost/thread/thread_time.hpp>

#include <future>
#include <thread>

namespace cthulhu {

typedef boost::interprocess::basic_string<char, std::char_traits<char>, CharAllocatorIPC>
    StreamTypeIPC;

typedef boost::interprocess::basic_string<char, std::char_traits<char>, CharAllocatorIPC>
    ProcessingStampKey;

typedef boost::interprocess::basic_string<char, std::char_traits<char>, CharAllocatorIPC>
    DynamicFieldName;

typedef boost::interprocess::
    allocator<std::pair<const ProcessingStampKey, double>, ManagedSHM::segment_manager>
        ProcessingStampsAllocType;

typedef boost::interprocess::
    map<ProcessingStampKey, double, std::less<ProcessingStampKey>, ProcessingStampsAllocType>
        ProcessingStampsIPC;

class StreamDescriptionIPC {
 public:
  StreamDescriptionIPC() = delete;
  StreamDescriptionIPC(const CharAllocatorIPC& alloc) : id(alloc), type(alloc) {}
  StreamIDIPC id;
  StreamTypeIPC type;
};

using RawDynamicIPC = RawDynamic<SharedPtrIPC>;

typedef boost::interprocess::allocator<RawDynamicIPC, ManagedSHM::segment_manager>
    RawDynamicIPCAllocType;

typedef boost::interprocess::vector<RawDynamicIPC, RawDynamicIPCAllocType> DynamicFields;

struct StreamSampleIPC {
  double timestamp;
  uint32_t sequenceNumber;
  std::variant<SharedPtrIPC, SharedPtrGPUIPC> payload;
  BufferType payloadType;
  uint32_t numberOfSubSamples;
  SharedPtrIPC parameters;
  ProcessingStampsIPC processingStamps;
  DynamicFields dynamicSampleParameters;

  StreamSampleIPC(ManagedSHM::segment_manager* mgr)
      : processingStamps(mgr), dynamicSampleParameters(mgr) {}
};

struct StreamConfigIPC {
  double nominalSampleRate;
  uint32_t sampleSizeInBytes;
  SharedPtrIPC parameters;
  DynamicFields dynamicConfigParameters;

  StreamConfigIPC(ManagedSHM::segment_manager* mgr) : dynamicConfigParameters(mgr) {}
};

class StreamConsumerIPC;
class StreamProducerIPC;

struct StreamConfigStampedIPC {
  explicit StreamConfigStampedIPC(const StreamConfigIPC& config) : data(config) {}
  StreamConfigIPC data;
  double timestamp = 0.0;
};

struct StreamSampleStampedIPC {
  explicit StreamSampleStampedIPC(const StreamSampleIPC& sample) : data(sample) {}
  StreamSampleIPC data;
  double timestamp = 0.0;
};

// This is the definiiton of a StreamInterface, for use in the IPC registry
class StreamInterfaceIPC {
  friend class StreamConsumerIPC;
  friend class StreamProducerIPC;

 public:
  // Non-copyable. Only one should exist, sitting in the Registry
  StreamInterfaceIPC(const StreamInterfaceIPC& other) = delete;
  StreamInterfaceIPC& operator=(const StreamInterfaceIPC& other) = delete;
  StreamInterfaceIPC(StreamInterfaceIPC&& other) = delete;
  StreamInterfaceIPC& operator=(StreamInterfaceIPC&& other) = delete;

  StreamInterfaceIPC() = delete;

  explicit StreamInterfaceIPC(const StreamDescriptionIPC& desc) : description_(desc){};

  const StreamDescriptionIPC& description() const {
    return description_;
  }

  bool advertised() const {
    return advertised_;
  }

  uint8_t numSubscribers() const {
    return numSubscribers_;
  }

 private:
  // Managed by the data lock
  std::optional<StreamConfigStampedIPC> config;
  uint8_t configConsumedCount = 0;
  std::optional<StreamSampleStampedIPC> sample;
  uint8_t sampleConsumedCount = 0;
  ConditionIPC dataUpdate;
  mutable MutexIPC dataLock;

  // These are to be controlled by the stream lock
  bool advertised_ = false;
  uint8_t numSubscribers_ = 0;
  mutable MutexIPC streamLock;

  const StreamDescriptionIPC description_;
};

class StreamConsumerIPC {
 public:
  explicit StreamConsumerIPC(
      StreamInterfaceIPC* si,
      const std::function<bool(const StreamConfigIPC& config)>& configCallback,
      const std::function<bool(const StreamSampleIPC& sampleData)>& sampleCallback,
      bool updateConfig = true);
  ~StreamConsumerIPC();

 private:
  void update();

  StreamInterfaceIPC* streamInterface_ = nullptr;
  std::thread thread_;
  std::function<bool(const StreamConfigIPC& config)> configCallback_;
  std::function<bool(const StreamSampleIPC& sampleData)> sampleCallback_;
  double latestSampleTime_ = 0.0;
  double latestConfigTime_ = 0.0;
  std::atomic<bool> stopSignal_;
};

class StreamProducerIPC {
 public:
  explicit StreamProducerIPC(StreamInterfaceIPC* si);

  ~StreamProducerIPC();

  void configure(const StreamConfigIPC& configIn);

  void publish(const StreamSampleIPC& sampleIn);

 private:
  void configureValid(const StreamConfigIPC& configIn);

  void publishValid(const StreamSampleIPC& sampleIn);

  void checkWaitForData(std::function<bool()> test);

  static constexpr unsigned int TIMEOUT_MILLISECONDS = 5;

  StreamInterfaceIPC* streamInterface_ = nullptr;
  bool valid_ = false;
};

} // namespace cthulhu
