// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <array>

#include <cthulhu/Aligner.h>
#include <cthulhu/Dispatcher.h>
#include <cthulhu/Framework.h>

namespace cthulhu {

// Convenience function for wrapping a universal reference into a unique pointer
// Useful for taking move-only node classes and getting them into unique_ptrs
template <class T>
std::unique_ptr<T> ptrWrap(T&& obj) {
  return std::make_unique<T>(std::forward<T>(obj));
}

template <typename T>
TypeInfoInterfacePtr sampleType() {
  auto type = Framework::instance().typeRegistry()->findSampleType(typeid(T));
  if (!type) {
    auto str = "Failed to lookup type in registry: " + std::string(typeid(T).name());
    XR_LOGCE("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  return type;
}

// Forward Declaration
class Context;

class NodeBase {
 public:
  NodeBase() = default;
  explicit NodeBase(bool initialized) : initialized_(initialized) {}
  virtual ~NodeBase() = default;
  // Users can check this bool on child classes (Subscriber, Transformer, etc) to ensure they didn't
  // have some error during initialization (such as a stream existing already).
  bool isInitialized() {
    return initialized_;
  }

 private:
  bool initialized_ = false;
};
using NodePtr = std::unique_ptr<NodeBase>;

// This is a handle for a basic subscriber (single input, no output) node. It can only
// be constructed by a Context
class Subscriber : public NodeBase {
 public:
  Subscriber& operator=(Subscriber&& other) = delete;
  Subscriber(Subscriber&& other) = default;

  Subscriber& operator=(const Subscriber& other) = delete;
  Subscriber(const Subscriber& other) = delete;

  virtual ~Subscriber() = default;

 private:
  explicit Subscriber(const StreamIDView& id, std::unique_ptr<StreamConsumer> consumer)
      : NodeBase(true), consumer_(std::move(consumer)), id_(id){};
  Subscriber(const StreamIDView& id) : id_(id){};
  std::unique_ptr<StreamConsumer> consumer_;
  StreamIDView id_;
  friend class Context;
};
using SubscriberPtr = std::unique_ptr<Subscriber>;

// This is a handle for a basic transformer (single input, single output) node. It can only
// be constructed by a Context
class Transformer : public NodeBase {
 public:
  Transformer& operator=(Transformer&& other) = delete;
  Transformer(Transformer&& other) = default;

  Transformer& operator=(const Transformer& other) = delete;
  Transformer(const Transformer& other) = delete;

  virtual ~Transformer() {
    // Must delete the consumer before the producer to prevent the consumer thread from
    // accessing the producer after it's deleted
    consumer_.reset();
    producer_.reset();
  };

 private:
  explicit Transformer(
      const StreamIDView& in,
      const StreamIDView& out,
      std::unique_ptr<StreamConsumer> consumer,
      std::unique_ptr<StreamProducer> producer)
      : NodeBase(true),
        consumer_(std::move(consumer)),
        producer_(std::move(producer)),
        in_(in),
        out_(out){};
  Transformer(const StreamIDView& in, const StreamIDView& out) : in_(in), out_(out){};
  std::unique_ptr<StreamConsumer> consumer_;
  std::unique_ptr<StreamProducer> producer_;
  StreamIDView in_;
  StreamIDView out_;
  friend class Context;
};
using TransformerPtr = std::unique_ptr<Transformer>;

// This is a handle for a basic publisher (no input, single output) node. It can only
// be constructed by a Context
class Publisher : public NodeBase {
 public:
  // Publish a sample on the stream
  template <typename T>
  bool publish(const T& sample);

  // Configure the stream
  template <typename T>
  bool configure(const T& configuration);

  inline bool isActive() const {
    return producer_ && producer_->isActive();
  };

  inline bool isConfigured() const {
    return producer_ && producer_->config();
  };

  // Allocate a sample for the stream from the sample pool
  template <typename T>
  T allocateSample(uint32_t numSubSamples = 1) const;

  Publisher& operator=(Publisher&& other) = delete;
  Publisher(Publisher&& other) = default;
  virtual ~Publisher() = default;

 private:
  explicit Publisher(const StreamIDView& id, std::unique_ptr<StreamProducer> producer)
      : NodeBase(true), producer_(std::move(producer)), id_(id){};
  Publisher(const StreamIDView& id) : id_(id){};
  std::unique_ptr<StreamProducer> producer_;
  StreamIDView id_;
  friend class Context;
};
using PublisherPtr = std::unique_ptr<Publisher>;

// This is a handle for a complex subscriber (multi input, no output) node. It can only
// be constructed by a Context
class MultiSubscriber : public NodeBase {
 public:
  MultiSubscriber& operator=(MultiSubscriber&& other) = delete;
  MultiSubscriber(MultiSubscriber&& other) = default;

  MultiSubscriber& operator=(const MultiSubscriber& other) = delete;
  MultiSubscriber(const MultiSubscriber& other) = delete;

  virtual ~MultiSubscriber() = default;

 private:
  explicit MultiSubscriber(
      const std::vector<StreamIDView>& ids,
      std::unique_ptr<AlignerBase> aligner)
      : NodeBase(true), aligner_(std::move(aligner)), ids_(ids){};
  MultiSubscriber(const std::vector<StreamIDView>& ids) : ids_(ids){};
  std::unique_ptr<AlignerBase> aligner_;
  const std::vector<StreamIDView> ids_;
  friend class Context;
};
using MultiSubscriberPtr = std::unique_ptr<MultiSubscriber>;

// This is a handle for a complex transformer (multi input, multi output) node. It can only
// be constructed by a Context
class MultiTransformer : public NodeBase {
 public:
  MultiTransformer& operator=(MultiTransformer&& other) = delete;
  MultiTransformer(MultiTransformer&& other) = default;

  MultiTransformer& operator=(const MultiTransformer& other) = delete;
  MultiTransformer(const MultiTransformer& other) = delete;

  virtual ~MultiTransformer() {
    // Must delete the aligner before the dispatcher to prevent the aligner thread from
    // accessing the producers on the dispatcher after they're deleted
    aligner_.reset();
    dispatcher_.reset();
  };

 private:
  explicit MultiTransformer(
      const std::vector<StreamIDView>& in,
      const std::vector<StreamIDView>& out,
      std::unique_ptr<AlignerBase> aligner,
      std::unique_ptr<Dispatcher> dispatcher)
      : NodeBase(true),
        aligner_(std::move(aligner)),
        dispatcher_(std::move(dispatcher)),
        in_(in),
        out_(out){};
  MultiTransformer(const std::vector<StreamIDView>& in, const std::vector<StreamIDView>& out)
      : in_(in), out_(out){};
  std::unique_ptr<AlignerBase> aligner_;
  std::unique_ptr<Dispatcher> dispatcher_;
  const std::vector<StreamIDView> in_;
  const std::vector<StreamIDView> out_;
  friend class Context;
};
using MultiTransformerPtr = std::unique_ptr<MultiTransformer>;

// This is a handle for a complex publisher (no input, multi output) node. It can only
// be constructed by a Context
class MultiPublisher : public NodeBase {
 public:
  // Publish samples on all streams
  template <typename... T>
  bool publish(const T&... samples);

  // Configure one of the streams, by index corresponding to the constructed order
  template <typename T>
  bool configure(const T& configuration, uint32_t streamNum);

  // Allocate a sample for one of the streams from the sample pool
  template <typename T>
  T allocateSample(uint32_t streamNum, uint32_t numSubSamples = 1) const;

  MultiPublisher(MultiPublisher&&) = default;
  MultiPublisher& operator=(MultiPublisher&&) = delete;

  MultiPublisher(const MultiPublisher&) = delete;
  MultiPublisher& operator=(const MultiPublisher&) = delete;

  virtual ~MultiPublisher() = default;

 private:
  explicit MultiPublisher(
      const std::vector<StreamIDView>& ids,
      std::unique_ptr<Dispatcher> dispatcher)
      : NodeBase(true), dispatcher_(std::move(dispatcher)), ids_(ids){};
  MultiPublisher(const std::vector<StreamIDView>& ids) : ids_(ids){};
  std::unique_ptr<Dispatcher> dispatcher_;
  const std::vector<StreamIDView> ids_;
  friend class Context;
};
using MultiPublisherPtr = std::unique_ptr<MultiPublisher>;

enum class ConsumerType : uint8_t { SYNC = 0, ASYNC = 1 };

enum class ProducerType : uint8_t { SYNC = 0, ASYNC = 1 };

enum class AlignerType : uint8_t { SYNC = 0, ASYNC = 1, CUSTOM = 2 };

enum class DispatcherType : uint8_t { SYNC = 0, ASYNC = 1, CUSTOM = 2 };

struct SubscriberOptions {
  ConsumerType consumerType = ConsumerType::SYNC;
};

struct PublisherOptions {
  ProducerType producerType = ProducerType::SYNC;
};

struct TransformerOptions {
  ConsumerType consumerType = ConsumerType::SYNC;
  ProducerType producerType = ProducerType::SYNC;
};

struct MultiSubscriberOptions {
  AlignerType alignerType = AlignerType::SYNC;
  std::unique_ptr<AlignerBase> alignerPtr;
};

struct MultiTransformerOptions {
  AlignerType alignerType = AlignerType::SYNC;
  DispatcherType dispatcherType = DispatcherType::SYNC;
  std::unique_ptr<AlignerBase> alignerPtr;
  std::unique_ptr<Dispatcher> dispatcherPtr;
};

// Class provided as a wrapper around StreamConfig to provide the setConfig() and getConfig()
// methods so templates don't break
class DefaultStreamConfig {
 public:
  DefaultStreamConfig() {}
  DefaultStreamConfig(const StreamConfig& config) : config_(config) {}

  const StreamConfig& getConfig() const {
    return config_;
  }

  void setConfig(const StreamConfig& config) {
    config_ = config;
  };

 private:
  StreamConfig config_;
};

// This is the API for interfacing with the Cthulhu Framework. It requires a context name, so that
// all interactions with the singleton Framework can be associated with a named context (e.g. a set
// of Nodes owned by the same functionality e.g. HW) It provides template construction functions for
// producing Nodes of different flavors by interfacing with the Stream Registry in the Framework.
class Context {
 public:
  explicit Context(const std::string& name, bool private_ns = false)
      : ctx_(Framework::instance().contextRegistry()->registerContext(name, private_ns)),
        name_(name),
        private_ns_(private_ns) {}

  Context(const Context& other)
      : ctx_(Framework::instance().contextRegistry()->registerContext(
            other.name_,
            other.private_ns_)),
        name_(other.name_),
        private_ns_(other.private_ns_) {}

  Context(Context&& other)
      : ctx_(other.ctx_), name_(std::move(other.name_)), private_ns_(other.private_ns_) {
    other.ctx_ = nullptr;
  }

  Context& operator=(const Context& other) {
    if (&other != this) {
      name_ = other.name_;
      private_ns_ = other.private_ns_;
      // Free the current context and then make a new one.
      Framework::instance().contextRegistry()->removeContext(ctx_);
      ctx_ = Framework::instance().contextRegistry()->registerContext(name_, private_ns_);
    }

    return *this;
  }

  Context& operator=(Context&& other) {
    name_ = std::move(other.name_);
    private_ns_ = other.private_ns_;
    ctx_ = other.ctx_;
    other.ctx_ = nullptr;

    return *this;
  }

  virtual ~Context() {
    if (ctx_ != nullptr) { // Might have become nulled if context is moved
      Framework::instance().contextRegistry()->removeContext(ctx_);
    }
  }

  inline StreamID applyNamespace(const StreamID& streamID) const {
    StreamID result = streamID;
    if (private_ns_) {
      result = name_ + "/" + streamID;
    }
    return result;
  }

  const std::string& name() const {
    return name_;
  }

  bool isPrivate() const {
    return private_ns_;
  }

  // Returns true if this stream ID is part of this context.
  // If this is not a private context, it always returns false.
  bool isInContext(const StreamID& streamID) const {
    return isPrivate() && streamID.size() > name_.size() &&
        streamID.substr(0, name_.size()) == name_;
  }

  // Template for constructing a subscriber
  template <typename T, typename U = DefaultStreamConfig>
  Subscriber subscribe(
      const StreamID& streamID,
      const std::function<void(const T&)>& sampleCallback,
      const std::function<bool(const U&)>& configCallback = nullptr,
      SubscriberOptions options = SubscriberOptions()) const;

  // Subscribe to a stream generically (untemplated)
  // A "specialization" of subscribe() is provided for T = StreamSample, U = StreamConfig. This case
  // handles users wishing to subscribe to generic data coming on the stream. The stream must
  // already exist, or an exception is thrown. Actually providing this as a template specialization
  // doesn't seem to be working correctly.
  //
  // Unsuccessful repro: https://our.internmc.facebook.com/intern/paste/P122967679/
  Subscriber subscribeGeneric(
      const StreamID& streamID,
      const std::function<void(const StreamSample&)>& sampleCallback,
      const std::function<bool(const StreamConfig&)>& configCallback = nullptr,
      SubscriberOptions options = SubscriberOptions()) const;

  // Subscribe to a stream generically (untemplated) with given type name.
  // As with the templated subscribe(...) calls, this will work even if the
  // stream doesn't already exist.
  Subscriber subscribeGeneric(
      const StreamID& streamID,
      const std::string& typeName,
      const std::function<void(const StreamSample&)>& sampleCallback,
      const std::function<bool(const StreamConfig&)>& configCallback = nullptr,
      SubscriberOptions options = SubscriberOptions()) const;

  // Template for constructing a transformer
  template <typename T, typename U, typename X>
  Transformer transform(
      const StreamID& inputID,
      const StreamID& outputID,
      const std::function<void(const T&, U&)>& sampleCallback,
      const std::function<bool(X&)>& configGenerator,
      TransformerOptions options = TransformerOptions()) const;
  template <typename T, typename U, typename W>
  Transformer transform(
      const StreamID& inputID,
      const StreamID& outputID,
      const std::function<void(const T&, U&)>& sampleCallback,
      const std::function<bool(const W&)>& configCallback,
      TransformerOptions options = TransformerOptions()) const;
  template <
      typename T,
      typename U,
      typename W = DefaultStreamConfig,
      typename X = DefaultStreamConfig>
  Transformer transform(
      const StreamID& inputID,
      const StreamID& outputID,
      const std::function<void(const T&, U&)>& sampleCallback,
      const std::function<bool(const W&, X&)>& configCallback = nullptr,
      TransformerOptions options = TransformerOptions()) const;

  // Template for constructing a publisher
  template <typename T>
  Publisher advertise(const StreamID& streamID, PublisherOptions options = PublisherOptions())
      const;
  // Alternatively, construct a publisher by just specifying the typeID for the stream.
  Publisher advertise(
      const StreamID& streamID,
      const uint32_t typeID,
      PublisherOptions options = PublisherOptions()) const;
  // Alternatively, construct a publisher by just specifying the type name for the stream.
  Publisher advertise(
      const StreamID& streamID,
      const std::string& typeName,
      PublisherOptions options = PublisherOptions()) const;

  // Template for constructing a multi-subscriber statically
  template <unsigned long N, typename... T, typename... U>
  MultiSubscriber subscribe(
      const std::array<StreamID, N>& streamIDs,
      const std::function<void(const T&...)>& callback,
      const std::function<bool(const U&...)>& configCallback = nullptr,
      MultiSubscriberOptions options = MultiSubscriberOptions()) const;

  // Template for constructing a multi-subscriber dynamically
  template <typename... T, typename... U>
  MultiSubscriber subscribe(
      const std::vector<std::vector<StreamID>>& streamIDs,
      const std::function<void(const T&...)>& callback,
      const std::function<bool(const U&...)>& configCallback = nullptr,
      MultiSubscriberOptions options = MultiSubscriberOptions()) const;
  template <typename... T, typename... U>
  MultiSubscriber subscribe(
      const std::vector<StreamID>& streamIDs,
      const std::function<void(const T&...)>& callback,
      const std::function<bool(const U&...)>& configCallback = nullptr,
      MultiSubscriberOptions options = MultiSubscriberOptions()) const;

  // Template for constructing a generic multisubscriber dynamically. Static usage not supported.
  // Grouped callbacks are also not supported. The aligner meta callbacks are taken explicitly since
  // the user is probably more likely to care about them if subscribing generically.
  MultiSubscriber subscribeGeneric(
      const std::vector<StreamID>& streamIDs,
      const std::function<void(const std::vector<StreamSample>&)>& sampleCallback,
      const std::function<bool(const std::vector<StreamConfig>&)>& configCallback = nullptr,
      const AlignerSamplesMetaCallback& samplesMetaCallback = nullptr,
      const AlignerConfigsMetaCallback& configsMetaCallback = nullptr,
      MultiSubscriberOptions options = MultiSubscriberOptions()) const;

  // Template for constructing a multi-transformer dynamically
  template <typename... T, typename... U>
  MultiTransformer transform(
      const std::vector<std::vector<StreamID>>& inputIDs,
      const std::vector<std::vector<StreamID>>& outputIDs,
      const std::function<void(T&...)>& sampleCallback,
      const std::function<bool(U&...)>& configCallback = nullptr,
      MultiTransformerOptions options = MultiTransformerOptions()) const;

  // Template for constructing a multi-publisher statically
  template <typename... T, unsigned long N>
  MultiPublisher advertise(const std::array<StreamID, N>& streamIDs) const;

  // Template for constructing a multi-publisher dynamically
  template <typename... T>
  MultiPublisher advertise(const std::vector<std::vector<StreamID>>& streamIDs) const;
  template <typename... T>
  MultiPublisher advertise(const std::vector<StreamID>& streamIDs) const;

  // Clock-Control API. Non-controllable clocks can be accessed with cthulhu::clock()
  inline const std::shared_ptr<ControllableClockInterface> getClockControl() const {
    return Framework::instance().clockManager()->controlClock(name_);
  };

 private:
  ContextInfoInterface* ctx_;
  std::string name_;
  bool private_ns_;
};

inline static const std::shared_ptr<ClockInterface> clock() {
  return Framework::instance().clockManager()->clock();
};

// This free function is provided as a replacement for isInContext, to avoid users creating a
// separate context (and locking a mutex or two) just to check some membership. It is identical to
// the following:
//
// const auto ctx = Context(name, private_ns);
// const auto in_context = ctx.isInContext(stream_id);
inline static bool
isStreamInContext(std::string_view stream_id, std::string_view name, bool private_ns) {
  return private_ns && stream_id.size() > name.size() && stream_id.substr(0, name.size()) == name;
}

// A configuration for streams that work with sample field on content block (SFoCB) samples
//
// SFoCB samples allocate their sample fields in a content block. In order to broadcast the
// size of that content block (sometimes called the 'payload' in implementation details), we need a
// configuration to carry the size. SFoCB config is a configuration for a SFoCB sample type.
// Use this to configure your SFoCB-sample-carrying stream.
//
// It is a user error if this is paired with a sample that's NOT using SFoCB.
class SFoCBConfig {
 public:
  // Type tag for invoking the templated SFoCB constructor
  template <class Sample>
  struct SampleType {};

  // Construct a SFoCBConfig that identifies samples for the type Sample.
  template <typename Sample>
  SFoCBConfig(SampleType<Sample>)
      : SFoCBConfig(Framework::instance().typeRegistry()->findSampleType(typeid(Sample))) {}

  // Construct a SFoCBConfig that identifies samples for the samples associated with the type ID
  SFoCBConfig(const uint32_t typeID);
  // Construct a SFoCBConfig that identifies samples for the samples associated with the type name
  SFoCBConfig(const std::string& typeName);

  //
  // Rest are implementation details that need to be public to play well
  // with rest of Cthulhu.
  //
  SFoCBConfig(const StreamConfig& config) : config_(config) {}

  inline const StreamConfig& getConfig() const {
    return config_;
  }

  inline void setConfig(const StreamConfig& config) {
    config_ = config;
  };

 private:
  SFoCBConfig(const TypeInfoInterfacePtr);
  StreamConfig config_;
};

} // namespace cthulhu

#include "ContextImpl.h"
