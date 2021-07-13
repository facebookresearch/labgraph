// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <assert.h>
#include <cstring>
#include <functional>
#include <future>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <queue>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

#include <cthulhu/BufferTypes.h>
#include <cthulhu/PerformanceMonitor.h>
#include <cthulhu/RawDynamic.h>

namespace cthulhu {

// StreamID is a string identifier that uniquely identifies a Stream
using StreamID = std::string;

// We started work on Cthulhu before we had C++17. We maintained our own
// lightweight version of std::string_view, called StreamIDView. But, now
// that we have C++17, and we've used the features throughout Cthulhu, it
// makes sense for us to use std::string_view.
using StreamIDView = std::string_view;

// A description of a stream holds both the StreamID and a type enum.
// These are used by the Framework's internal API when requesting a Stream from the Registry.
// When the Framework constructs a StreamInterface in the Registry, the Description will be passed
// to it, and it will be owned by the StreamInterface. There should only be two StreamID instances
// in the system: 1: the mapping in the Registry and 2: the Description held by the StreamInterface.
// All other usages should be SteamIDView's derived from this Description.
// For this reason, the StreamID and type can never be modified.
class StreamDescription {
 private:
  const StreamID id_;
  const uint32_t type_;

 public:
  // Construct from a StreamID and a type
  StreamDescription(const StreamID& id, uint32_t type) : id_(id), type_(type){};

  // Get a read-only StreamID
  inline const StreamID& id() const {
    return id_;
  };

  // Get a read-only type
  inline const uint32_t& type() const {
    return type_;
  };
};

// This is a header providing the basic metadata associated with a sample.
struct SampleHeader {
  double timestamp;
  uint32_t sequenceNumber;
};

// This is an additional header providing processing timing of Nodes in producing a Sample.
// It should only be auto-populated by the Framework
using ProcessingStamps = std::map<std::string, double>;

struct SampleMetadata;

using SampleHistory = std::map<StreamIDView, std::shared_ptr<SampleMetadata>>;

// The full metadata contains the sample header, processing stamps, and history pointers
// to the metadata of input samples. These pointers can be traced to obtain a full history
// of information that went into producing the sample, as well as the processing timing.
struct SampleMetadata {
  // Basic metadata
  SampleHeader header;

  // User-determined processing stamps
  ProcessingStamps processingStamps;

  // Pointers to metadata from ancestors
  SampleHistory history;
};

// A Stream Sample contains metadata and a payload.
// Both are to be created by buffers from the Sample Pool
struct StreamSample {
  StreamSample();

  // The full historical metadata of the sample
  std::shared_ptr<SampleMetadata> metadata;

  // This is the bulk content block data. Can be CPU or GPU.
  AnyBuffer payload;
  // This specifies how many repeating subsamples are represented within the content block
  uint32_t numberOfSubSamples = 0;

  // This carries any lighter-weight data fields
  CpuBuffer parameters;

  // This carries any dynamically-sized parameters
  SharedRawDynamicArray dynamicParameters;
};

// When adding new fields to StreamConfig, make sure to modify StreamConfigEquality.h/.cpp
struct StreamConfig {
  StreamConfig() = default;
  StreamConfig(CpuBuffer parameterData) : parameters(parameterData) {}
  StreamConfig(size_t staticFieldSize, size_t dynamicFieldSize) {
    if (staticFieldSize > 0) {
      parameters = CpuBuffer(new uint8_t[staticFieldSize](), std::default_delete<uint8_t[]>());
    }
    if (dynamicFieldSize > 0) {
      dynamicParameters = makeSharedRawDynamicArray(dynamicFieldSize);
    }
  }

  double nominalSampleRate = 0.0;
  uint32_t sampleSizeInBytes = 1;

  // This carries customizable data fields
  CpuBuffer parameters;

  // This carries any dynamically-sized parameters
  SharedRawDynamicArray dynamicParameters;
};

using SampleCallback = std::function<void(const StreamSample&)>;
using ConfigCallback = std::function<bool(const StreamConfig&)>;

struct DataVariant {
  enum class Type { SAMPLE, CONFIG, INVALID } type = Type::INVALID;
  StreamSample sample;
  StreamConfig config;
};

// Forward Declaration
class StreamInterface;

// This is the interface to be used for producing signals on a stream.
// It is constructed with a pointer to a StreamInterface which lives in the Stream
// Registry and thus has process lifetime. It will hook-in to the stream interface as
// the producer, which will fail if the StreamInterface already has a producer. Ownership
// of this producer will be transferred from the Context to a created Node (Publisher or
// Transformer)
class StreamProducer {
 public:
  // Attempts to hook into the StreamInterface
  explicit StreamProducer(StreamInterface* si, bool async = false);

  // Unhook's from the StreamInterface (if it was hooked successfully on construction)
  virtual ~StreamProducer();

  // These are the signals that can be sent to the StreamInterface

  // This sends a sample to active Consumers
  void produceSample(const StreamSample& sample) const;

  // Configuration will move the StreamConfig onto the interface, which
  // will be provided to active Consumers, or eventually hooked Consumers
  void configureStream(const StreamConfig& config) const;

  // This gets the current configuration for the stream
  const StreamConfig* config() const;

  // This will return false if the Producer was constructed on a Stream with an existing Producer
  inline bool isActive() const {
    return producedStream_ != nullptr;
  };

 protected:
  StreamInterface* producedStream_ = nullptr;

  bool async_;

  std::thread thread_;
  std::promise<void> stopSignal_;
  mutable std::mutex queueMutex_;
  mutable std::queue<DataVariant> queue_;
  static constexpr int MAX_QUEUE_SIZE = 100;
};

// This is the interface to be used for consuming signals on a stream.
// It is constructed with a pointer to a StreamInterface which lives in the Stream
// Registry and thus has process lifetime. It will hook-in to the StreamInterface as a
// consumer, which will never fail (no limit on the number of consumers on a stream). The callback
// function for each signal must be specified on construction. Only the SampleCallback is required.
// The public signal receive functions shall be called by the StreamInterface that was hooked.
class StreamConsumer {
 public:
  // Hooks into the StreamInterface and stores callbacks
  explicit StreamConsumer(
      StreamInterface* si,
      SampleCallback callback,
      ConfigCallback configCallback = nullptr,
      bool async = false);

  // Unhooks from the StreamInterface
  virtual ~StreamConsumer();

  // These are the signals that can be received from the StreamInterface

  // Calls the sample callback
  void consumeSample(const StreamSample& sample) const;

  // Calls the configuration callback (if set). If one already exists on the stream,
  // it will be immediately called on hookConsumer (in the constructor). The configCallback_
  // is set in the initializer list prior to hookConsumer, so this is just fine.
  void receiveConfig(const StreamConfig& config) const;

  PerformanceSummary getPerformanceSummary() const;

  uint64_t getQueueCapacity() const;
  void setQueueCapacity(uint64_t capacity);

 protected:
  StreamInterface* consumedStream_ = nullptr;
  SampleCallback callback_;
  ConfigCallback configCallback_;

  mutable bool inhibitSampleCallback_ = false;

  bool async_;

  std::thread thread_;
  std::promise<void> stopSignal_;
  mutable PerformanceMonitor performanceMonitor_;
  mutable std::mutex queueMutex_;
  mutable std::queue<DataVariant> queue_;
  uint64_t queueCapacity_;
  static constexpr uint64_t DEFAULT_QUEUE_CAPACITY = 10;
};

// This is the interface used to represent a stream. A single instance for each stream lives in the
// Stream Registry within a process. Producers/Consumers and constructed that hook-in to the stream,
// and Producers call a set of signal interface functions. These signal functions pass the signal on
// to all hooked-in Consumers. Signals and hooks are locked and thread-safe, so new references can
// be hooked-in concurrently with signaling.
class StreamInterface {
 public:
  // Constructs given a description, which cannot be changed
  explicit StreamInterface(const StreamDescription& desc) : description_(desc){};
  // This won't have ownership of any of the hooked producers or consumers. But it
  // only exists in the Singleton Registry, so it will live longer than any of them
  virtual ~StreamInterface() = default;

  // Gets the read-only description
  inline const StreamDescription& description() const {
    return description_;
  };

  // Sets the paused flag to on/off
  inline void setPaused(bool paused) {
    paused_ = paused;
  };

  // Non-copyable. Only one should exist, sitting in the Registry
  StreamInterface(const StreamInterface& other) = delete;
  StreamInterface& operator=(const StreamInterface& other) = delete;

  // Move-constructable, only for insertion into the Registry
  StreamInterface(StreamInterface&& other)
      : description_(other.description_), config_(other.config_), paused_(other.paused_) {
    std::lock_guard<std::timed_mutex> lock(other.timed_mutex_);
    producer_ = std::move(other.producer_);
    consumers_ = std::move(other.consumers_);
  };
  // Non move assignable, shouldn't be needed
  StreamInterface& operator=(StreamInterface&& other) = delete;

  const StreamProducer* producer() const {
    return producer_;
  };
  const std::vector<const StreamConsumer*> consumers() const {
    return consumers_;
  };

  const StreamConfig& config() const {
    return config_;
  };

  inline bool isConfigured() const {
    return configured_;
  };

 protected:
  // Signal interfaces, should only be called by the producer
  // These lock the mutex to ensure that consumers are not hooked/unhooked while sending signals.
  // Additional signals can be added, along with flavors of Producer/Consumer that can use them
  virtual bool sendSample(const StreamSample& sample) = 0;
  virtual bool configure(const StreamConfig& config) = 0;

  // Hook, unhook functions, should only be called by Producer/Consumer constructors/destructors
  // These lock the mutex to modify the set of consumers and producer
  virtual bool hookProducer(const StreamProducer* const producer) = 0;
  virtual void hookConsumer(const StreamConsumer* const consumer) = 0;
  virtual void removeProducer(const StreamProducer* const producer) = 0;
  virtual void removeConsumer(const StreamConsumer* const consumer) = 0;

  const StreamDescription description_;

  // The latest config sits on the interface, so it can be pushed to any new Consumers
  StreamConfig config_;

  // This holds the reference to the producer, so it knows who is responsible for sending signals.
  const StreamProducer* producer_ = nullptr;

  // This holders the references to all consumers, so it knows where to send signals
  std::vector<const StreamConsumer*> consumers_;

  // Used to lock the producer/consumers
  // Timed to allow timeouts during IPC deadlocks
  mutable std::timed_mutex timed_mutex_;

  // Flag for whether to inhibit signals, not locked by mutex. Defaults to non-paused
  bool paused_ = false;

  bool configured_ = false;

  // Friend these classes to restrict hook/unhook and signaling APIs
  friend class StreamProducer;
  friend class StreamConsumer;
}; // class StreamInterface

} // namespace cthulhu
