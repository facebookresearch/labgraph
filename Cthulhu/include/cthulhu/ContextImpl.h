// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <logging/LogChannel.h>

#include <numeric>
#include <sstream>

#include "ContextImpl_details.h"

namespace cthulhu {

template <typename T>
bool Publisher::publish(const T& sample) {
  if (!producer_ || !producer_->isActive() ||
      !Framework::instance().typeRegistry()->findSampleType(typeid(T))) {
    XR_LOGCW(
        "Cthulhu",
        "Publish failed. Producer is {}null, Producer is {}active. Sample type is {}defined.",
        producer_ ? "NOT " : "",
        (producer_ && producer_->isActive()) ? "" : "NOT ",
        !Framework::instance().typeRegistry()->findSampleType(typeid(T)) ? "NOT " : "");
    return false;
  }
  producer_->produceSample(sample.getSample());
  return true;
};

// Specialization provided for generic StreamSample. We trust the user knows what they're doing here
// since it's impossible to check for type match.
template <>
bool Publisher::publish<StreamSample>(const StreamSample& sample);

template <class T>
bool Publisher::configure(const T& configuration) {
  if (!producer_) {
    return false;
  }
  producer_->configureStream(configuration.getConfig());
  return true;
};

// Specialization provided for generic StreamConfig. We trust the user knows what they're doing here
// since it's impossible to check for type match.
template <>
bool Publisher::configure<StreamConfig>(const StreamConfig& configuration);

template <typename T>
T Publisher::allocateSample(uint32_t numSubSamples) const {
  if (!producer_ || !Framework::instance().typeRegistry()->findSampleType(typeid(T))) {
    auto str = "Attempted to allocate sample on an invalid publisher.";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  return details::allocateSampleHelper<T>(producer_->config(), id_, numSubSamples);
};

template <typename... T>
bool MultiPublisher::publish(const T&... args) {
  std::vector<StreamSample> samplesUnflat(ids_.size());
  bool success = details::SampleUncaster<T...>::uncast(samplesUnflat, 0, args...);
  dispatcher_->dispatchSamples(samplesUnflat);
  return success;
};

template <class T>
bool MultiPublisher::configure(const T& configuration, uint32_t streamNum) {
  if (!dispatcher_) {
    return false;
  }
  const StreamConfig& config = configuration.getConfig();
  dispatcher_->configureStream(config, streamNum);
  return true;
};

template <typename T>
T MultiPublisher::allocateSample(uint32_t streamNum, uint32_t numSubSamples) const {
  if (!dispatcher_) {
    auto str = "Attempted to allocate sample on an invalid multi-publisher.";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  if (streamNum >= ids_.size()) {
    auto str = "Attempted to allocate sample on an invalid publisher.";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  return details::allocateSampleHelper<T>(
      dispatcher_->streamConfig(streamNum), ids_[streamNum], numSubSamples);
};

template <typename T, typename U>
Subscriber Context::subscribe(
    const StreamID& streamIDRaw,
    const std::function<void(const T&)>& sampleCallback,
    const std::function<bool(const U&)>& configCallback,
    SubscriberOptions options) const {
  StreamID streamID = applyNamespace(streamIDRaw);
  static_assert(
      std::is_constructible<T, const StreamSample&>::value,
      "Context::subscribe requires that sample type T is constructed with const StreamSample&");
  static_assert(
      std::is_constructible<U, const StreamConfig&>::value,
      "Context::subscribe requires that configuration type U is constructed with const StreamConfig&");
  // Make sure the stream is valid
  if (!std::is_same<U, DefaultStreamConfig>::value &&
      !Framework::instance().typeRegistry()->isValidStreamType(typeid(T), typeid(U))) {
    auto str = "Stream/Config Mismatch";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }

  // Get Types
  auto type = sampleType<T>();

  // Make sure we're not trying to use a configCallback on a basic stream
  if (type->isBasic() && configCallback != nullptr) {
    auto str = "Attempted to provide config callback on basic stream type";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }

  // Create Callbacks
  SampleCallback scallback = [sampleCallback](const StreamSample& sample) -> void {
    const T data(sample);
    sampleCallback(data);
  };
  ConfigCallback ccallback = [configCallback](const StreamConfig& config) -> bool {
    const U streamConfig(config);
    return configCallback(streamConfig);
  };
  if (configCallback == nullptr) {
    ccallback = nullptr;
  }

  // Get Streams from Registry
  StreamDescription desc{streamID, type->typeID()};
  auto si = Framework::instance().streamRegistry()->registerStream(desc);
  if (type->typeID() != si->description().type()) {
    // Type mismatch detected
    XR_LOGCW(
        "Cthulhu", "Type mismatch detected [{}, {}]", type->typeID(), si->description().type());
    return Subscriber(si->description().id());
  }

  // Create Consumer
  std::unique_ptr<StreamConsumer> consumer(
      new StreamConsumer(si, scallback, ccallback, options.consumerType == ConsumerType::ASYNC));

  // Return Node
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register single subscriber against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  const auto& sid = si->description().id();
  ctx_->registerSubscriber(std::vector<StreamID>{sid});
  return Subscriber(sid, std::move(consumer));
};

template <typename T, typename U, typename W>
Transformer Context::transform(
    const StreamID& inputID,
    const StreamID& outputID,
    const std::function<void(const T&, U&)>& sampleCallback,
    const std::function<bool(const W&)>& configAcceptor,
    TransformerOptions options) const {
  auto type = sampleType<U>();

  if (!type->isBasic()) {
    auto str = "Attempted to ignore config on non-basic stream type";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  std::function<bool(const W&, DefaultStreamConfig&)> configCallback =
      [configAcceptor](const W& input, DefaultStreamConfig&) -> bool {
    return configAcceptor(input);
  };
  return transform(inputID, outputID, sampleCallback, configCallback, std::move(options));
};

template <typename T, typename U, typename X>
Transformer Context::transform(
    const StreamID& inputID,
    const StreamID& outputID,
    const std::function<void(const T&, U&)>& sampleCallback,
    const std::function<bool(X&)>& configGenerator,
    TransformerOptions options) const {
  auto type = sampleType<T>();

  if (!type->isBasic()) {
    auto str = "Attempted to ignore config on non-basic stream type";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  std::function<bool(const DefaultStreamConfig&, X&)> configCallback =
      [configGenerator](const DefaultStreamConfig&, X& output) -> bool {
    return configGenerator(output);
  };
  return transform(inputID, outputID, sampleCallback, configCallback, std::move(options));
};

template <typename T, typename U, typename W, typename X>
Transformer Context::transform(
    const StreamID& inputIDRaw,
    const StreamID& outputIDRaw,
    const std::function<void(const T&, U&)>& sampleCallback,
    const std::function<bool(const W&, X&)>& configCallback,
    TransformerOptions options) const {
  StreamID inputID = applyNamespace(inputIDRaw);
  StreamID outputID = applyNamespace(outputIDRaw);
  static_assert(
      std::is_constructible<T, const StreamSample&>::value,
      "Context::transform requires that sample type T is constructed with const StreamSample&");
  static_assert(
      std::is_constructible<W, const StreamConfig&>::value,
      "Context::transform requires that configuration type W is constructed with const StreamConfig&");

  // Make sure the streams are valid
  if ((!std::is_same<W, DefaultStreamConfig>::value &&
       !Framework::instance().typeRegistry()->isValidStreamType(typeid(T), typeid(W))) ||
      (!std::is_same<X, DefaultStreamConfig>::value &&
       !Framework::instance().typeRegistry()->isValidStreamType(typeid(U), typeid(X)))) {
    auto str = "Stream/Config Mismatch";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }

  // Get Types
  auto typeIn = sampleType<T>();

  StreamDescription descIn{inputID, typeIn->typeID()};
  auto siIn = Framework::instance().streamRegistry()->registerStream(descIn);
  auto typeOut = sampleType<U>();

  // Get Stream from Registry
  StreamDescription descOut{outputID, typeOut->typeID()};
  auto siOut = Framework::instance().streamRegistry()->registerStream(descOut);
  if (typeIn->typeID() != siIn->description().type() ||
      typeOut->typeID() != siOut->description().type()) {
    // Type mismatch detected
    XR_LOGCW(
        "Cthulhu",
        "Type mismatch detected [{}, {}] [{}, {}]",
        typeIn,
        siIn->description().type(),
        typeOut,
        siOut->description().type());
    return Transformer(siIn->description().id(), siOut->description().id());
  }

  // Create Producer
  std::unique_ptr<StreamProducer> producer(
      new StreamProducer(siOut, options.producerType == ProducerType::ASYNC));

  // Create Callbacks
  auto scallback = [sampleCallback,
                    producer = producer.get(),
                    &inID = siIn->description().id(),
                    &outID = siOut->description().id()](const StreamSample& in) -> void {
    const T inData(in);
    if (!producer->config()) {
      XR_LOGCW("Cthulhu", "Transformer callback not executing, output stream not configured.");
      return;
    }
    U outData = details::allocateSampleHelper<U>(producer->config(), outID);
    // TBD: What to do if callback needs to determine numSubSamples?
    sampleCallback(inData, outData);

    auto& out = outData.getSample();
    out.metadata->history.emplace(inID, in.metadata);
    producer->produceSample(out);
  };
  ConfigCallback ccallback = [configCallback,
                              producer = producer.get()](const StreamConfig& in) -> bool {
    const W inData(in);
    X outData;
    bool success = configCallback(inData, outData);
    if (!success) {
      return false;
    }
    const StreamConfig& out = outData.getConfig();
    producer->configureStream(out);
    return true;
  };
  if (configCallback == nullptr) {
    ccallback = nullptr;
  }

  // Create Consumer
  std::unique_ptr<StreamConsumer> consumer(
      new StreamConsumer(siIn, scallback, ccallback, options.consumerType == ConsumerType::ASYNC));

  // Return Node
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register single transformer against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  const auto& inId = siIn->description().id();
  const auto& outId = siOut->description().id();
  ctx_->registerTransformer(std::vector<StreamID>{inId}, std::vector<StreamID>{outId});
  return Transformer(inId, outId, std::move(consumer), std::move(producer));
};

template <typename T>
Publisher Context::advertise(const StreamID& streamIDRaw, PublisherOptions options) const {
  return advertise(streamIDRaw, sampleType<T>()->typeID(), options);
};

template <unsigned long N, typename... T, typename... U>
MultiSubscriber Context::subscribe(
    const std::array<StreamID, N>& streamIDs,
    const std::function<void(const T&...)>& callback,
    const std::function<bool(const U&...)>& configCallback,
    MultiSubscriberOptions options) const {
  // Create Aligner
  auto aligner = details::alignerFromOptions(options.alignerType, std::move(options.alignerPtr));

  // Get Types and Validate
  std::array<uint32_t, N> types;
  details::SampleTypesStatic<T...>::template getTypes<0>(types);
  std::array<bool, N> basicStreams;
  for (unsigned long i = 0; i < N; ++i) {
    auto type = Framework::instance().typeRegistry()->findTypeID(types[i]);
    if (!type) {
      auto str = "Attempted to lookup unregistered typeID: " + std::to_string(types[i]);
      XR_LOGCE("Cthulhu", "{}", str);
      throw std::runtime_error(str);
    }
    basicStreams[i] = type->isBasic();
  }

  // Create Callbacks and Register in Aligner
  std::function<void(const std::vector<StreamSample>&, const T&...)> callbackAppended =
      [callback](const std::vector<StreamSample>&, const T&... args) -> void { callback(args...); };
  AlignerSampleCallback cb = details::generateAlignerCallback<0>(callbackAppended);
  aligner->setCallback(cb);
  if (configCallback != nullptr) {
    std::function<bool(const std::vector<StreamConfig>&, const U&...)> configCallbackAppended =
        [configCallback](const std::vector<StreamConfig>&, const U&... args) -> bool {
      return configCallback(args...);
    };
    AlignerConfigCallback ccb =
        details::generateAlignerConfigCallback<0>(configCallbackAppended, basicStreams);
    aligner->setConfigCallback(ccb);
  }

  // Get Streams from Registry and Load in Aligner
  std::vector<StreamIDView> streamIDsVec;
  streamIDsVec.reserve(N);
  for (unsigned long i = 0; i < N; i++) {
    StreamID streamID = applyNamespace(streamIDs[i]);
    auto type = Framework::instance().typeRegistry()->findTypeID(types[i]);
    StreamDescription desc{streamID, types[i]};
    auto si = Framework::instance().streamRegistry()->registerStream(desc);
    if (types[i] != si->description().type()) {
      // Type mismatch detected
      XR_LOGCW("Cthulhu", "Type mismatch detected [{}, {}]", types[i], si->description().type());
      return MultiSubscriber(streamIDsVec);
    }
    streamIDsVec.push_back(StreamIDView(si->description().id()));
    aligner->registerConsumer(si, i);
  }
  aligner->finalize();

  // Return Node
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register multi subscriber against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  ctx_->registerSubscriber(streamIDsVec);
  return MultiSubscriber(streamIDsVec, std::move(aligner));
};

template <typename... T, typename... U>
MultiSubscriber Context::subscribe(
    const std::vector<std::vector<StreamID>>& streamIDs,
    const std::function<void(const T&...)>& callback,
    const std::function<bool(const U&...)>& configCallback,
    MultiSubscriberOptions options) const {
  // Flatten StreamIDs
  std::vector<StreamID> streamIDsFlat;
  std::vector<unsigned long> groups(streamIDs.size());
  for (int groupIdx = 0; groupIdx < streamIDs.size(); ++groupIdx) {
    std::vector<StreamID> streamIDsNS(streamIDs[groupIdx].size());
    for (int elemIdx = 0; elemIdx < streamIDs[groupIdx].size(); ++elemIdx) {
      streamIDsNS[elemIdx] = applyNamespace(streamIDs[groupIdx][elemIdx]);
    }
    groups[groupIdx] = streamIDs[groupIdx].size();
    streamIDsFlat.insert(streamIDsFlat.end(), streamIDsNS.begin(), streamIDsNS.end());
  }

  // Get Types
  std::vector<uint32_t> types(streamIDsFlat.size(), 0);
  details::SampleTypesDynamic<T...>::getTypes(groups, 0, 0, types);
  std::vector<bool> basicStreams(streamIDsFlat.size());
  for (size_t i = 0; i < basicStreams.size(); ++i) {
    auto type = Framework::instance().typeRegistry()->findTypeID(types[i]);
    if (!type) {
      auto str = "Attempted to lookup unregistered typeID: " + std::to_string(types[i]);
      XR_LOGCE("Cthulhu", "{}", str);
      throw std::runtime_error(str);
    }
    basicStreams[i] = type->isBasic();
  }

  // Create Aligner
  auto aligner = details::alignerFromOptions(options.alignerType, std::move(options.alignerPtr));

  // Create Callbacks and Register in Aligner
  std::function<void(const std::vector<StreamSample>&, const T&...)> callbackAppended =
      [callback](const std::vector<StreamSample>&, const T&... args) -> void { callback(args...); };
  AlignerSampleCallback cb = details::generateAlignerCallback<0>(0, groups, callbackAppended);
  aligner->setCallback(cb);
  if (configCallback != nullptr) {
    std::function<bool(const std::vector<StreamConfig>&, const U&...)> configCallbackAppended =
        [configCallback](const std::vector<StreamConfig>&, const U&... args) -> bool {
      return configCallback(args...);
    };
    AlignerConfigCallback ccb =
        details::generateAlignerConfigCallback<0>(0, groups, configCallbackAppended, basicStreams);
    aligner->setConfigCallback(ccb);
  }

  // Get Streams from Registry and Load in Aligner
  std::vector<StreamIDView> streamIDsVec;
  streamIDsVec.reserve(streamIDsFlat.size());
  for (unsigned long i = 0; i < streamIDsFlat.size(); i++) {
    auto type = Framework::instance().typeRegistry()->findTypeID(types[i]);
    StreamDescription desc{streamIDsFlat[i], types[i]};
    auto si = Framework::instance().streamRegistry()->registerStream(desc);
    if (types[i] != si->description().type()) {
      // Type mismatch detected
      XR_LOGCW("Cthulhu", "Type mismatch detected [{}, {}]", types[i], si->description().type());
      return MultiSubscriber(streamIDsVec);
    }
    streamIDsVec.push_back(StreamIDView(si->description().id()));
    aligner->registerConsumer(si, i);
  }
  aligner->finalize();

  // Return Node
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register multi subscriber against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  ctx_->registerSubscriber(streamIDsVec);
  return MultiSubscriber(streamIDsVec, std::move(aligner));
};

template <typename... T, typename... U>
MultiSubscriber Context::subscribe(
    const std::vector<StreamID>& streamIDs,
    const std::function<void(const T&...)>& callback,
    const std::function<bool(const U&...)>& configCallback,
    MultiSubscriberOptions options) const {
  std::vector<std::vector<StreamID>> streamIDsGrouped(1);
  streamIDsGrouped[0] = streamIDs;
  return subscribe(streamIDsGrouped, callback, configCallback, std::move(options));
};

template <typename... T, typename... U>
MultiTransformer Context::transform(
    const std::vector<std::vector<StreamID>>& inputIDs,
    const std::vector<std::vector<StreamID>>& outputIDs,
    const std::function<void(T&...)>& sampleCallback,
    const std::function<bool(U&...)>& configCallback,
    MultiTransformerOptions options) const {
  // Flatten StreamIDs
  std::vector<StreamID> inputIDsFlat;
  std::vector<StreamID> outputIDsFlat;
  std::vector<unsigned long> groups(inputIDs.size() + outputIDs.size());
  for (int groupIdx = 0; groupIdx < groups.size(); ++groupIdx) {
    if (groupIdx < inputIDs.size()) {
      std::vector<StreamID> inputIDsNS(inputIDs[groupIdx].size());
      for (int elemIdx = 0; elemIdx < inputIDs[groupIdx].size(); ++elemIdx) {
        inputIDsNS[elemIdx] = applyNamespace(inputIDs[groupIdx][elemIdx]);
      }
      groups[groupIdx] = inputIDs[groupIdx].size();
      inputIDsFlat.insert(inputIDsFlat.end(), inputIDsNS.begin(), inputIDsNS.end());
    } else {
      int modIdx = groupIdx - inputIDs.size();
      std::vector<StreamID> outputIDsNS(outputIDs[modIdx].size());
      for (int elemIdx = 0; elemIdx < outputIDs[modIdx].size(); ++elemIdx) {
        outputIDsNS[elemIdx] = applyNamespace(outputIDs[modIdx][elemIdx]);
      }
      groups[groupIdx] = outputIDs[modIdx].size();
      outputIDsFlat.insert(outputIDsFlat.end(), outputIDsNS.begin(), outputIDsNS.end());
    }
  }

  // Get Types
  std::vector<uint32_t> allTypes(inputIDsFlat.size() + outputIDsFlat.size(), 0);
  details::SampleTypesDynamic<T...>::getTypes(groups, 0, 0, allTypes);
  std::vector<bool> basicStreams(allTypes.size());
  for (size_t i = 0; i < basicStreams.size(); ++i) {
    auto type = Framework::instance().typeRegistry()->findTypeID(allTypes[i]);
    if (!type) {
      auto str = "Attempted to lookup unregistered typeID: " + std::to_string(allTypes[i]);
      XR_LOGCE("Cthulhu", "{}", str);
      throw std::runtime_error(str);
    }
    basicStreams[i] = type->isBasic();
  }

  // Create Aligner
  auto aligner = details::alignerFromOptions(options.alignerType, std::move(options.alignerPtr));

  // Create Dispatcher
  auto dispatcher = std::make_unique<Dispatcher>();

  // Create Callbacks and Register in Aligner
  std::function<void(
      const std::vector<StreamID>&,
      const std::vector<StreamSample>&,
      std::vector<StreamSample>&,
      T&...)>
      callbackAppended = [sampleCallback](
                             const std::vector<StreamID>&,
                             const std::vector<StreamSample>&,
                             std::vector<StreamSample>&,
                             T&... args) -> void { sampleCallback(args...); };

  AlignerSampleCallback cb = details::generateAlignerCallback<0>(
      dispatcher.get(), 0, 0, inputIDsFlat, outputIDsFlat, groups, callbackAppended);
  aligner->setCallback(cb);

  if (configCallback != nullptr) {
    std::function<bool(const std::vector<StreamConfig>&, std::vector<StreamConfig>&, U&...)>
        configCallbackAppended = [configCallback](
                                     const std::vector<StreamConfig>&,
                                     std::vector<StreamConfig>&,
                                     U&... args) -> bool { return configCallback(args...); };

    AlignerConfigCallback ccb = details::generateAlignerConfigCallback<0>(
        dispatcher.get(), 0, 0, outputIDsFlat.size(), groups, configCallbackAppended, basicStreams);
    aligner->setConfigCallback(ccb);
  }

  // Get Input Streams from Registry and Load into Aligner
  std::vector<StreamIDView> inputIDsVec;
  inputIDsVec.reserve(inputIDsFlat.size());
  std::vector<StreamIDView> outputIDsVec;
  outputIDsVec.reserve(outputIDsFlat.size());
  for (unsigned long i = 0; i < inputIDsFlat.size(); i++) {
    StreamDescription desc{inputIDsFlat[i], allTypes[i]};
    auto si = Framework::instance().streamRegistry()->registerStream(desc);
    if (allTypes[i] != si->description().type()) {
      // Type mismatch detected
      XR_LOGCW("Cthulhu", "Type mismatch detected [{}, {}]", allTypes[i], si->description().type());
      return MultiTransformer(inputIDsVec, outputIDsVec);
    }
    inputIDsVec.push_back(StreamIDView(si->description().id()));
    aligner->registerConsumer(si, i);
  }

  // Get Output Streams from Registry and Load into Dispatcher
  for (unsigned long i = 0; i < outputIDsFlat.size(); i++) {
    StreamDescription desc{outputIDsFlat[i], allTypes[i + inputIDsFlat.size()]};
    auto si = Framework::instance().streamRegistry()->registerStream(desc);
    if (allTypes[i + inputIDsFlat.size()] != si->description().type()) {
      // Type mismatch detected
      XR_LOGCW(
          "Cthulhu",
          "Out Type mismatch detected [{}, {}]",
          allTypes[i + inputIDsFlat.size()],
          si->description().type());
      return MultiTransformer(inputIDsVec, outputIDsVec);
    }
    outputIDsVec.push_back(StreamIDView(si->description().id()));
    dispatcher->registerProducer(si);
  }
  aligner->finalize();

  // Return Node
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register multi transformer against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }

  ctx_->registerTransformer(inputIDsVec, outputIDsVec);
  return MultiTransformer(inputIDsVec, outputIDsVec, std::move(aligner), std::move(dispatcher));
};

template <typename... T, unsigned long N>
MultiPublisher Context::advertise(const std::array<StreamID, N>& streamIDs) const {
  // Create Dispatcher
  std::unique_ptr<Dispatcher> dispatcher = std::make_unique<Dispatcher>();

  // Get Types
  std::array<uint32_t, N> types;
  details::SampleTypesStatic<T...>::template getTypes<0>(types);

  // Get Streams from Registry and Load in Dispatcher
  std::vector<StreamIDView> streamIDsVec;
  streamIDsVec.reserve(N);
  for (unsigned long i = 0; i < N; i++) {
    StreamID streamID = applyNamespace(streamIDs[i]);
    StreamDescription desc{streamID, types[i]};
    auto si = Framework::instance().streamRegistry()->registerStream(desc);
    if (types[i] != si->description().type()) {
      // Type mismatch detected
      XR_LOGCW("Cthulhu", "Type mismatch detected [{}, {}]", types[i], si->description().type());
      return MultiPublisher(streamIDsVec);
    }
    streamIDsVec.push_back(StreamIDView(si->description().id()));
    dispatcher->registerProducer(si);
  }

  // Return Node
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register multi publisher against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  ctx_->registerPublisher(streamIDsVec);
  return MultiPublisher(streamIDsVec, std::move(dispatcher));
};

template <typename... T>
MultiPublisher Context::advertise(const std::vector<std::vector<StreamID>>& streamIDs) const {
  // Flatten StreamIDs
  std::vector<StreamID> streamIDsFlat;
  std::vector<unsigned long> groups(streamIDs.size());
  for (int groupIdx = 0; groupIdx < streamIDs.size(); ++groupIdx) {
    std::vector<StreamID> streamIDsNS(streamIDs[groupIdx].size());
    for (int elemIdx = 0; elemIdx < streamIDs[groupIdx].size(); ++elemIdx) {
      streamIDsNS[elemIdx] = applyNamespace(streamIDs[groupIdx][elemIdx]);
    }
    groups[groupIdx] = streamIDs[groupIdx].size();
    streamIDsFlat.insert(streamIDsFlat.end(), streamIDsNS.begin(), streamIDsNS.end());
  }

  // Create Dispatcher
  std::unique_ptr<Dispatcher> dispatcher = std::make_unique<Dispatcher>();

  // Get Types
  std::vector<uint32_t> types(streamIDsFlat.size());
  details::SampleTypesDynamic<T...>::getTypes(groups, 0, 0, types);

  // Get Streams from Registry and Load in Dispatcher
  std::vector<StreamIDView> streamIDsVec;
  streamIDsVec.reserve(streamIDsFlat.size());
  for (unsigned long i = 0; i < streamIDsFlat.size(); i++) {
    StreamDescription desc{streamIDsFlat[i], types[i]};
    auto si = Framework::instance().streamRegistry()->registerStream(desc);
    if (types[i] != si->description().type()) {
      // Type mismatch detected
      XR_LOGCW("Cthulhu", "P Type mismatch detected [{}, {}]", types[i], si->description().type());
      return MultiPublisher(streamIDsVec);
    }
    streamIDsVec.push_back(StreamIDView(si->description().id()));
    dispatcher->registerProducer(si);
  }

  // Return Node
  if (ctx_ == nullptr) {
    const auto err = "Attempted to register multi publisher against null context";
    XR_LOGCE("Cthulhu", "{}", err);
    throw std::runtime_error(err);
  }
  ctx_->registerPublisher(streamIDsVec);
  return MultiPublisher(streamIDsVec, std::move(dispatcher));
};

template <typename... T>
MultiPublisher Context::advertise(const std::vector<StreamID>& streamIDs) const {
  std::vector<std::vector<StreamID>> streamIDsGrouped(1);
  streamIDsGrouped[0] = streamIDs;
  return advertise<T...>(streamIDsGrouped);
};

} // namespace cthulhu
