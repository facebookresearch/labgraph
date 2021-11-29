#include <cthulhu/Context.h>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

Subscriber Context::subscribeGeneric(
    const StreamID& streamIDRaw,
    const std::function<void(const StreamSample&)>& sampleCallback,
    const std::function<bool(const StreamConfig&)>& configCallback,
    SubscriberOptions options) const {
  StreamID streamID = applyNamespace(streamIDRaw);

  // When subscribing generically, the stream must exist already. If the stream does not exist,
  // there's no way to just subscribe generically since there wouldn't be any type information.
  // Throw an exception if the stream does not exist.
  auto* stream = Framework::instance().streamRegistry()->getStream(streamID);
  if (stream == nullptr) {
    // Choose to return an inactive Subscriber here rather than throw an exception, since this a
    // user error and not an error with Cthulhu.
    XR_LOGCW(
        "Cthulhu",
        "Attempted to register generic single subscriber without topic {} existing already",
        streamID);
    return Subscriber(streamID);
  }

  // Make sure we're not trying to use a configCallback on a basic stream
  const auto typeID = stream->description().type();
  const auto typeInfo = Framework::instance().typeRegistry()->findTypeID(typeID);
  if (typeInfo->isBasic() && configCallback != nullptr) {
    // This is still user error, but an exception is thrown here to maintain consistency with the
    // config callback checks in the rest of the Cthulhu codebase.
    auto str = "Attempted to provide config callback on basic stream type";
    XR_LOGCE("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }

  // Now that the callbacks match the stream, add a StreamConsumer for it. We can directly pass the
  // callbacks that we received from the caller since no type conversions need to happen.
  std::unique_ptr<StreamConsumer> consumer(new StreamConsumer(
      stream, sampleCallback, configCallback, options.consumerType == ConsumerType::ASYNC));

  // Finally, register against the context registry and return a new subscriber.
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register generic single subscriber against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  const auto& sid = stream->description().id();
  ctx_->registerSubscriber(std::vector<StreamID>{sid});
  return Subscriber(sid, std::move(consumer));
}

Subscriber Context::subscribeGeneric(
    const StreamID& streamIDRaw,
    const std::string& typeName,
    const std::function<void(const StreamSample&)>& sampleCallback,
    const std::function<bool(const StreamConfig&)>& configCallback,
    SubscriberOptions options) const {
  StreamID streamID = applyNamespace(streamIDRaw);

  // Get Type
  auto type = Framework::instance().typeRegistry()->findTypeName(typeName);
  if (!type) {
    auto str = "Failed to lookup type in registry: " + std::string(typeName);
    XR_LOGCE("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }

  // Make sure we're not trying to use a configCallback on a basic stream
  if (type->isBasic() && configCallback != nullptr) {
    auto str = "Attempted to provide config callback on basic stream type";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }

  // Get Streams from Registry
  StreamDescription desc{streamID, type->typeID()};
  auto si = Framework::instance().streamRegistry()->registerStream(desc);
  if (type->typeID() != si->description().type()) {
    // Type mismatch detected
    XR_LOGCW(
        "Cthulhu",
        "Type mismatch detected [stream ID: {}; Requested type ID: {} ({}). Actual type ID: {}]",
        streamID,
        type->typeID(),
        type->typeName(),
        si->description().type());
    return Subscriber(si->description().id());
  }

  // Now that the callbacks match the stream, add a StreamConsumer for it. We can directly pass the
  // callbacks that we received from the caller since no type conversions need to happen.
  std::unique_ptr<StreamConsumer> consumer(new StreamConsumer(
      si, sampleCallback, configCallback, options.consumerType == ConsumerType::ASYNC));

  // Finally, register against the context registry and return a new subscriber.
  if (ctx_ == nullptr) {
    const auto err =
        "Attempted to register generic single subscriber with type name against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  const auto& sid = si->description().id();
  ctx_->registerSubscriber(std::vector<StreamID>{sid});
  return Subscriber(sid, std::move(consumer));
}

MultiSubscriber Context::subscribeGeneric(
    const std::vector<StreamID>& streamIDs,
    const std::function<void(const std::vector<StreamSample>&)>& sampleCallback,
    const std::function<bool(const std::vector<StreamConfig>&)>& configCallback,
    const AlignerSamplesMetaCallback& samplesMetaCallback,
    const AlignerConfigsMetaCallback& configsMetaCallback,
    MultiSubscriberOptions options) const {
  // Apply namespace to all streamIDs
  std::vector<StreamID> streamIDs_ns;
  streamIDs_ns.reserve(streamIDs.size());
  for (const auto& id : streamIDs) {
    streamIDs_ns.emplace_back(applyNamespace(id));
  }

  // Ensure that all streamIDs exist already, and that they're all non-basic. Streams must exist
  // since they cannot be created without type information, and they must all be non-basic to allow
  // configurations to get propagated correctly with the default aligner.
  std::vector<StreamInterface*> streams;
  streams.reserve(streamIDs_ns.size());
  for (const auto& streamID : streamIDs_ns) {
    auto* stream = Framework::instance().streamRegistry()->getStream(streamID);
    // Ensure stream exists
    if (stream == nullptr) {
      // Choose to return an inactive MultiSubscriber here rather than throw an exception, since
      // this is a user error and not an error with Cthulhu.
      XR_LOGCW(
          "Cthulhu",
          "{}",
          "Attempted to register generic multi subscriber without topic {} existing already.",
          streamID);
      // Need to create a vector of StreamIDViews since there's no StreamID vector constructor.
      std::vector<StreamIDView> streamIDs_view;
      streamIDs_view.reserve(streamIDs.size());
      for (const auto& id : streamIDs) {
        streamIDs_view.emplace_back(id);
      }
      return MultiSubscriber(streamIDs_view);
    }

    const auto typeID = stream->description().type();
    const auto typeInfo = Framework::instance().typeRegistry()->findTypeID(typeID);
    if (typeInfo->isBasic() && (configCallback != nullptr || configsMetaCallback != nullptr)) {
      // This is still user error, but an exception is thrown here to maintain consistency with the
      // config callback checks in the rest of the Cthulhu codebase.
      auto str = "Found a basic stream when given config callback";
      XR_LOGCE("Cthulhu", "{}", str);
      throw std::runtime_error(str);
    }
    streams.push_back(stream);
  }

  // Hook up the aligner using the options provided by the user.
  auto aligner = details::alignerFromOptions(options.alignerType, std::move(options.alignerPtr));
  aligner->setCallback(sampleCallback);
  aligner->setConfigCallback(configCallback);
  aligner->setSamplesMetaCallback(samplesMetaCallback);
  aligner->setConfigsMetaCallback(configsMetaCallback);

  std::vector<StreamIDView> streamID_views;
  streamID_views.reserve(streamIDs_ns.size());
  for (size_t i = 0; i < streamIDs_ns.size(); ++i) {
    aligner->registerConsumer(streams[i], i);
    streamID_views.push_back(streams[i]->description().id());
  }
  aligner->finalize();

  // Finally, register against the context registry and return a new multi subscriber.
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register generic multi subscriber against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  ctx_->registerSubscriber(streamID_views);
  return MultiSubscriber(streamID_views, std::move(aligner));
}

Publisher Context::advertise(
    const StreamID& streamIDRaw,
    const uint32_t typeID,
    PublisherOptions options) const {
  StreamID streamID = applyNamespace(streamIDRaw);

  // Get Stream from Registry
  StreamDescription desc{streamID, typeID};
  auto si = Framework::instance().streamRegistry()->registerStream(desc);
  if (typeID != si->description().type()) {
    // Type mismatch detected
    XR_LOGCW("Cthulhu", "Type mismatch detected [{}, {}]", typeID, si->description().type());
    return Publisher(si->description().id());
  }

  // Create Producer
  std::unique_ptr<StreamProducer> producer(
      new StreamProducer(si, ProducerType::ASYNC == options.producerType));

  // Return Node
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register single publisher against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  const auto& sid = si->description().id();
  ctx_->registerPublisher(std::vector<StreamID>{sid});
  return Publisher(sid, std::move(producer));
}

Publisher Context::advertise(
    const StreamID& streamIDRaw,
    const std::string& typeName,
    PublisherOptions options) const {
  auto typeInfo = Framework::instance().typeRegistry()->findTypeName(typeName);
  if (!typeInfo) {
    const auto err = std::string("Attempted to register stream with unrecognized type name \"") +
        typeName + std::string("\"");
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }

  return advertise(streamIDRaw, typeInfo->typeID(), options);
}

template <>
bool Publisher::publish<StreamSample>(const StreamSample& sample) {
  if (!producer_ || !producer_->isActive()) {
    XR_LOGCW(
        "Cthulhu",
        "Publish failed. Producer is {}null, Producer is {}active.",
        producer_ ? "NOT " : "",
        (producer_ && producer_->isActive()) ? "" : "NOT ");
  }

  producer_->produceSample(sample);
  return true;
}

template <>
bool Publisher::configure<StreamConfig>(const StreamConfig& configuration) {
  if (!producer_) {
    return false;
  }

  producer_->configureStream(configuration);
  return true;
}

SFoCBConfig::SFoCBConfig(const uint32_t typeID) try
    : SFoCBConfig(Framework::instance().typeRegistry()->findTypeID(typeID)) {
} catch (...) {
  XR_LOGE("No type info found with type ID '{}'", typeID);
  throw;
}

SFoCBConfig::SFoCBConfig(const std::string& typeName) try
    : SFoCBConfig(Framework::instance().typeRegistry()->findTypeName(typeName)) {
} catch (...) {
  // TODO(ianmcintyre) this failes to compile, and I don't know why...
  // XR_LOGE("No type info found with type name {}", typeName);
  throw;
}

SFoCBConfig::SFoCBConfig(const TypeInfoInterfacePtr typeInfo) {
  if (!typeInfo) {
    throw std::runtime_error("Cthulhu type info not found!");
  } else {
    config_.sampleSizeInBytes = typeInfo->sampleParameterSize();
  }
}

} // namespace cthulhu
