// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <type_traits>

namespace cthulhu {

namespace details {

// This is a utility for allocating a sample from the Framework.
template <typename T>
T allocateSampleHelper(
    const StreamConfig* const config,
    const StreamIDView& id,
    uint32_t numSubSamples = 1) {
  static_assert(
      std::is_base_of_v<AutoStreamSample, T>,
      "cthulhu::details::allocateSampleHelper only supports types that subclas cthulhu::AutoStreamSample");

  if (!config) {
    auto str = "Attempted to allocate sample on an unconfigured stream.";
    XR_LOGCE("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  const bool hasSamplesInContentBlock = cthulhu::Framework::instance()
                                            .typeRegistry()
                                            ->findSampleType(typeid(T))
                                            ->hasSamplesInContentBlock();

  size_t payloadSize = config->sampleSizeInBytes * numSubSamples;
  StreamSample uncastedSample;
  uncastedSample.payload = Framework::instance().memoryPool()->getBufferFromPool(id, payloadSize);
  uncastedSample.numberOfSubSamples = numSubSamples;

  T sample{uncastedSample, hasSamplesInContentBlock};
  sample.allocated();
  return sample;
};

// This helper class gets the size of an object if it is an array, othersize returns size 1
template <typename>
struct ArraySize;
template <typename T, size_t N>
struct ArraySize<std::array<T, N>> {
  static size_t const size = N;
};
// Default case if its not an array
template <typename T>
struct ArraySize {
  static size_t const size = 1;
};

// This helper class is used to resize an object if it is a vector, otherwise assert that
// the resize operation is to size 1
template <class>
struct ResizeHelper;
template <class T>
struct ResizeHelper<std::vector<T>> {
  static void resize(std::vector<T>& arg, size_t size) {
    arg.resize(size);
  };
};
template <class T>
struct ResizeHelper {
  static void resize(T& arg, size_t size) {
    assert(size == 1);
  };
};

// Similar to ResizeHelper, but this can be used on a Sample Type to both resize the
// vector and allocate a sample, given its StreamID.
template <class>
struct ResizeAllocHelper;
template <class T>
struct ResizeAllocHelper<std::vector<T>> {
  static void resize(
      std::vector<T>& arg,
      size_t size,
      Dispatcher* dispatcher,
      unsigned long idx,
      const std::vector<StreamID>& ids) {
    arg.resize(size);
    for (const auto& id : ids) {
      arg[idx] = details::allocateSampleHelper<T>(dispatcher->streamConfig(idx), id);
      idx++;
    }
  };
};
template <class T>
struct ResizeAllocHelper {
  static void resize(
      T& arg,
      size_t size,
      Dispatcher* dispatcher,
      unsigned long idx,
      const std::vector<StreamID>& ids) {
    assert(size == 1);
    arg = details::allocateSampleHelper<T>(dispatcher->streamConfig(idx), ids[0]);
  };
};

// These cast generic samples to typed samples statically (for sizes known at compile time)
template <unsigned long offset, unsigned long groupSize, typename T>
void sampleCaster(
    const std::vector<StreamSample>& samples,
    std::array<T, groupSize>& castedSamples) {
  if (samples.size() < (offset + groupSize - 1)) {
    throw std::exception();
  }
  for (unsigned long i = 0; i < groupSize; i++) {
    const auto& sample = samples[offset + i];
    castedSamples[i].setSample(sample);
  }
};
template <unsigned long offset, typename T>
void sampleCaster(const std::vector<StreamSample>& samples, T& castedSample) {
  if (samples.size() < (offset)) {
    throw std::exception();
  }
  const auto& sample = samples[offset];
  castedSample.setSample(sample);
};

// These cast generic samples to typed samples dynamically (for sizes known at run time)
template <typename T>
void sampleCaster(
    unsigned long offset,
    unsigned long groupSize,
    const std::vector<StreamSample>& samples,
    std::vector<T>& castedSamples) {
  // Resize the castedSamples output here, since this is where we can be sure
  // that they are a vector type
  castedSamples.resize(groupSize);
  if (samples.size() < (offset + groupSize - 1)) {
    throw std::exception();
  }
  for (unsigned long i = 0; i < groupSize; i++) {
    const auto& sample = samples[offset + i];
    castedSamples[i].setSample(sample);
  }
};
template <typename T>
void sampleCaster(
    unsigned long offset,
    unsigned long groupSize,
    const std::vector<StreamSample>& samples,
    T& castedSample) {
  if (groupSize != 1 || samples.size() < offset) {
    throw std::exception();
  }
  const auto& sample = samples[offset];
  castedSample.setSample(sample);
};

// These cast generic configs to typed configs statically (for sizes known at compile time)
template <unsigned long offset, unsigned long groupSize, typename T>
void configCaster(
    const std::vector<StreamConfig>& configs,
    std::array<T, groupSize>& castedConfigs,
    unsigned long skipOffset) {
  if (configs.size() < (offset + groupSize - 1)) {
    throw std::exception();
  }
  for (unsigned long i = 0; i < groupSize; i++) {
    const auto& config = configs[offset + skipOffset + i];
    castedConfigs[i].setConfig(config);
  }
};
template <unsigned long offset, typename T>
void configCaster(
    const std::vector<StreamConfig>& configs,
    T& castedConfig,
    unsigned long skipOffset) {
  if (configs.size() < (offset)) {
    throw std::exception();
  }
  const auto& config = configs[offset + skipOffset];
  castedConfig.setConfig(config);
};

// These cast generic configs to typed configs dynamically (for sizes known at run time)
template <typename T>
void configCaster(
    unsigned long offset,
    unsigned long groupSize,
    const std::vector<StreamConfig>& configs,
    std::vector<T>& castedConfigs) {
  // Resize the castedConfigs output here, since this is where we can be sure
  // that they are a vector type
  castedConfigs.resize(groupSize);
  if (configs.size() < (offset + groupSize - 1)) {
    throw std::exception();
  }
  for (unsigned long i = 0; i < groupSize; i++) {
    const auto& config = configs[offset + i];
    castedConfigs[i].setConfig(config);
  }
};
template <typename T>
void configCaster(
    unsigned long offset,
    unsigned long groupSize,
    const std::vector<StreamConfig>& configs,
    T& castedConfig) {
  if (groupSize != 1 || configs.size() < offset) {
    throw std::exception();
  }
  const auto& config = configs[offset];
  castedConfig.setConfig(config);
};

// These uncast typed samples to generic samples dynamically (for sizes known at run time)
// Variadic templates allow for this to be called on parameter groupings of vectors and regular
// samples TBD: Would need to add support for array types in order to directly publish an array
// object
template <typename... T>
struct SampleUncaster;
template <typename T>
struct SampleUncaster<std::vector<T>> {
  static bool uncast(
      std::vector<StreamSample>& samplesUnflat,
      unsigned long offset,
      const std::vector<T>& samples) {
    if (samplesUnflat.size() != offset + samples.size() ||
        !Framework::instance().typeRegistry()->findSampleType(typeid(T))) {
      return false;
    }
    for (unsigned long i = 0; i < samples.size(); i++) {
      const StreamSample& streamSamp = samples[i].getSample();
      samplesUnflat[offset + i] = streamSamp;
    }

    return true;
  };
};
template <typename T>
struct SampleUncaster<T> {
  static bool
  uncast(std::vector<StreamSample>& samplesUnflat, unsigned long offset, const T& sample) {
    if (samplesUnflat.size() != (offset + 1) ||
        !Framework::instance().typeRegistry()->findSampleType(typeid(T))) {
      return false;
    }
    const StreamSample& streamSamp = sample.getSample();
    samplesUnflat[offset] = streamSamp;

    return true;
  };
};
template <typename T, typename... other>
struct SampleUncaster<std::vector<T>, other...> {
  static bool uncast(
      std::vector<StreamSample>& samplesUnflat,
      unsigned long offset,
      const std::vector<T>& samples,
      const other&... others) {
    if (samplesUnflat.size() < offset + samples.size() ||
        !Framework::instance().typeRegistry()->findSampleType(typeid(T))) {
      return false;
    }
    for (unsigned long i = 0; i < samples.size(); i++) {
      const StreamSample& streamSamp = samples[i].getSample();
      samplesUnflat[offset + i] = streamSamp;
    }

    return SampleUncaster<other...>::uncast(samplesUnflat, offset + samples.size(), others...);
  };
};
template <typename T, typename... other>
struct SampleUncaster<T, other...> {
  static bool uncast(
      std::vector<StreamSample>& samplesUnflat,
      unsigned long offset,
      const T& sample,
      const other&... others) {
    if (samplesUnflat.size() <= offset ||
        !Framework::instance().typeRegistry()->findSampleType(typeid(T))) {
      return false;
    }
    const StreamSample& streamSamp = sample.getSample();
    samplesUnflat[offset] = streamSamp;

    return SampleUncaster<other...>::uncast(samplesUnflat, offset + 1, others...);
  };
};

// These uncast typed configs to generic configs dynamically (for sizes known at run time)
// Variadic templates allow for this to be called on parameter groupings of vectors and regular
// samples. The variadic form is currently not used in MultiPublisher, since the configure()
// function configures one stream at a time
template <typename... T>
struct ConfigUncaster;
template <typename T>
struct ConfigUncaster<std::vector<T>> {
  static bool uncast(
      std::vector<StreamConfig>& configsUnflat,
      unsigned long offset,
      const std::vector<T>& configs) {
    if (configsUnflat.size() != offset + configs.size() ||
        !Framework::instance().typeRegistry()->findConfigType(typeid(T))) {
      return false;
    }
    for (unsigned long i = 0; i < configs.size(); i++) {
      const StreamConfig streamConf(configs[i].getConfig());
      configsUnflat[offset + i] = streamConf;
    }

    return true;
  };
};
template <typename T>
struct ConfigUncaster<T> {
  static bool
  uncast(std::vector<StreamConfig>& configsUnflat, unsigned long offset, const T& config) {
    if (configsUnflat.size() != (offset + 1) ||
        !Framework::instance().typeRegistry()->findConfigType(typeid(T))) {
      return false;
    }
    const StreamConfig streamConf(config.getConfig());
    configsUnflat[offset] = streamConf;

    return true;
  };
};
template <typename T, typename... other>
struct ConfigUncaster<std::vector<T>, other...> {
  static bool uncast(
      std::vector<StreamConfig>& configsUnflat,
      unsigned long offset,
      const std::vector<T>& configs,
      const other&... others) {
    if (configsUnflat.size() < offset + configs.size() ||
        !Framework::instance().typeRegistry()->findConfigType(typeid(T))) {
      return false;
    }
    for (unsigned long i = 0; i < configs.size(); i++) {
      const StreamConfig streamConf(configs[i].getConfig());
      configsUnflat[offset + i] = streamConf;
    }

    return ConfigUncaster<other...>::uncast(configsUnflat, offset + configs.size(), others...);
  };
};
template <typename T, typename... other>
struct ConfigUncaster<T, other...> {
  static bool uncast(
      std::vector<StreamConfig>& configsUnflat,
      unsigned long offset,
      const T& config,
      const other&... others) {
    if (configsUnflat.size() <= offset ||
        !Framework::instance().typeRegistry()->findConfigType(typeid(T))) {
      return false;
    }
    const StreamConfig streamConf(config.getConfig());
    configsUnflat[offset] = streamConf;

    return ConfigUncaster<other...>::uncast(configsUnflat, offset + 1, others...);
  };
};

// Gets the typeid's of a parameter pack mixing regular and vector types
template <typename T>
struct SampleTypesDynamicHelper {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    if (groups.size() <= groupNumber || groups[groupNumber] + offset > types.size()) {
      throw std::exception();
    }
    for (unsigned long i = 0; i < groups[groupNumber]; i++) {
      types[offset + i] = Framework::instance().typeRegistry()->findSampleType(typeid(T))->typeID();
    }
    return;
  }
};
template <typename T>
struct SampleTypesDynamicHelper<std::vector<T>> {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    if (groups.size() <= groupNumber || groups[groupNumber] + offset > types.size()) {
      throw std::exception();
    }
    for (unsigned long in = 0; in < groups[groupNumber]; in++) {
      types[offset + in] =
          Framework::instance().typeRegistry()->findSampleType(typeid(T))->typeID();
    }
    return;
  }
};
template <typename T>
struct SampleTypesDynamicHelper<const std::vector<T>> {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    if (groups.size() <= groupNumber || groups[groupNumber] + offset > types.size()) {
      throw std::exception();
    }
    for (unsigned long in = 0; in < groups[groupNumber]; in++) {
      types[offset + in] =
          Framework::instance().typeRegistry()->findSampleType(typeid(T))->typeID();
    }
    return;
  }
};

template <typename... T>
struct SampleTypesDynamic;
template <typename T>
struct SampleTypesDynamic<T> {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    SampleTypesDynamicHelper<T>::getTypes(groups, groupNumber, offset, types);
  }
};
template <typename T, typename... other>
struct SampleTypesDynamic<T, other...> {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    SampleTypesDynamicHelper<T>::getTypes(groups, groupNumber, offset, types);
    SampleTypesDynamic<other...>::getTypes(
        groups, groupNumber + 1, offset + groups[groupNumber], types);
  }
};

// Gets the typeid's of a parameter pack mixing regular and vector types
template <typename T>
struct ConfigTypesDynamicHelper {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    if (groups.size() <= groupNumber || groups[groupNumber] + offset > types.size()) {
      throw std::exception();
    }
    for (unsigned long i = 0; i < groups[groupNumber]; i++) {
      types[offset + i] = Framework::instance().typeRegistry()->findConfigType(typeid(T))->typeID();
    }
    return;
  }
};
template <typename T>
struct ConfigTypesDynamicHelper<std::vector<T>> {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    if (groups.size() <= groupNumber || groups[groupNumber] + offset > types.size()) {
      throw std::exception();
    }
    for (unsigned long in = 0; in < groups[groupNumber]; in++) {
      types[offset + in] =
          Framework::instance().typeRegistry()->findConfigType(typeid(T))->typeID();
    }
    return;
  }
};
template <typename T>
struct ConfigTypesDynamicHelper<const std::vector<T>> {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    if (groups.size() <= groupNumber || groups[groupNumber] + offset > types.size()) {
      throw std::exception();
    }
    for (unsigned long in = 0; in < groups[groupNumber]; in++) {
      types[offset + in] =
          Framework::instance().typeRegistry()->findConfigType(typeid(T))->typeID();
    }
    return;
  }
};

template <typename... T>
struct ConfigTypesDynamic;
template <typename T>
struct ConfigTypesDynamic<T> {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    ConfigTypesDynamicHelper<T>::getTypes(groups, groupNumber, offset, types);
  }
};
template <typename T, typename... other>
struct ConfigTypesDynamic<T, other...> {
  static void getTypes(
      const std::vector<unsigned long>& groups,
      unsigned long groupNumber,
      unsigned long offset,
      std::vector<uint32_t>& types) {
    ConfigTypesDynamicHelper<T>::getTypes(groups, groupNumber, offset, types);
    ConfigTypesDynamic<other...>::getTypes(
        groups, groupNumber + 1, offset + groups[groupNumber], types);
  }
};

// Gets the typeid's of a parameter pack mixing regular and array types
template <typename... T>
struct SampleTypesStatic;
template <typename T, unsigned long N>
struct SampleTypesStatic<std::array<T, N>> {
  template <unsigned long offset, unsigned long M>
  static void getTypes(std::array<uint32_t, M>& types) {
    static_assert((offset + N) <= M, "SampleTypesStatic::getTypes out of bounds");
    for (unsigned long i = 0; i < N; i++) {
      types[offset + i] = Framework::instance().typeRegistry()->findSampleType(typeid(T))->typeID();
    }
  }
};
template <typename T>
struct SampleTypesStatic<T> {
  template <unsigned long offset, unsigned long M>
  static void getTypes(std::array<uint32_t, M>& types) {
    static_assert(offset <= M, "SampleTypesStatic::getTypes out of bounds");
    types[offset] = Framework::instance().typeRegistry()->findSampleType(typeid(T))->typeID();
  }
};
template <typename T, unsigned long N, typename... other>
struct SampleTypesStatic<std::array<T, N>, other...> {
  template <unsigned long offset, unsigned long M>
  static void getTypes(std::array<uint32_t, M>& types) {
    static_assert((offset + N) <= M, "SampleTypesStatic::getTypes out of bounds");
    for (unsigned long i = 0; i < N; i++) {
      types[offset + i] = Framework::instance().typeRegistry()->findSampleType(typeid(T))->typeID();
    }
    return SampleTypesStatic<other...>::getTypes<offset + N>(types);
  }
};
template <typename T, typename... other>
struct SampleTypesStatic<T, other...> {
  template <unsigned long offset, unsigned long M>
  static void getTypes(std::array<uint32_t, M>& types) {
    static_assert(offset <= M, "SampleTypesStatic::getTypes out of bounds");
    types[offset] = Framework::instance().typeRegistry()->findSampleType(typeid(T))->typeID();
    return SampleTypesStatic<other...>::getTypes<offset + 1>(types);
  }
};

// Gets the typeid's of a parameter pack mixing regular and array types
template <typename... T>
struct ConfigTypesStatic;
template <typename T>
struct ConfigTypesStatic<T> {
  template <unsigned long offset, unsigned long M>
  static void getTypes(std::array<uint32_t, M>& types) {
    static_assert(offset <= M, "ConfigTypesStatic::getTypes out of bounds");
    types[offset] = Framework::instance().typeRegistry()->findConfigType(typeid(T))->typeID();
  }
};
template <typename T, unsigned long N>
struct ConfigTypesStatic<std::array<T, N>> {
  template <unsigned long offset, unsigned long M>
  static void getTypes(std::array<uint32_t, M>& types) {
    static_assert((offset + N) <= M, "ConfigTypesStatic::getTypes out of bounds");
    for (unsigned long i = 0; i < N; i++) {
      types[offset + i] = Framework::instance().typeRegistry()->findConfigType(typeid(T))->typeID();
    }
  }
};
template <typename T, unsigned long N, typename... other>
struct ConfigTypesStatic<std::array<T, N>, other...> {
  template <unsigned long offset, unsigned long M>
  static void getTypes(std::array<uint32_t, M>& types) {
    static_assert((offset + N) <= M, "ConfigTypesStatic::getTypes out of bounds");
    for (unsigned long i = 0; i < N; i++) {
      types[offset + i] = Framework::instance().typeRegistry()->findConfigType(typeid(T))->typeID();
    }
    return ConfigTypesStatic<other...>::getTypes<offset + N>(types);
  }
};
template <typename T, typename... other>
struct ConfigTypesStatic<T, other...> {
  template <unsigned long offset, unsigned long M>
  static void getTypes(std::array<uint32_t, M>& types) {
    static_assert(offset <= M, "ConfigTypesStatic::getTypes out of bounds");
    types[offset] = Framework::instance().typeRegistry()->findConfigType(typeid(T))->typeID();
    return ConfigTypesStatic<other...>::getTypes<offset + 1>(types);
  }
};

// Generate Aligner Sample Callbacks using Compile-time groupings
template <unsigned long offset, typename T>
AlignerSampleCallback generateAlignerCallback(
    const std::function<void(const std::vector<StreamSample>&, const T&)>& callback) {
  AlignerSampleCallback alignerCallback =
      [callback](const std::vector<StreamSample>& samples) -> void {
    T castedSamples;
    sampleCaster<offset>(samples, castedSamples);
    callback(samples, castedSamples);
  };
  return alignerCallback;
};
template <unsigned long offset, typename T, typename... other>
AlignerSampleCallback generateAlignerCallback(
    const std::function<void(const std::vector<StreamSample>&, const T&, const other&...)>&
        callback) {
  std::function<void(const std::vector<StreamSample>&, const other&...)> callbackReduced =
      [callback](const std::vector<StreamSample>& samples, const other&... args) -> void {
    T castedSamples;
    sampleCaster<offset>(samples, castedSamples);
    callback(samples, castedSamples, args...);
  };
  return generateAlignerCallback<offset + ArraySize<T>::size>(callbackReduced);
};

// Generate Aligner Sample Callbacks using Run-time groupings
template <unsigned long groupNumber, typename T>
AlignerSampleCallback generateAlignerCallback(
    unsigned long offset,
    const std::vector<unsigned long>& groupSizes,
    const std::function<void(const std::vector<StreamSample>&, const T&)>& callback) {
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  AlignerSampleCallback alignerCallback = [callback, offset, groupSize = groupSizes[groupNumber]](
                                              const std::vector<StreamSample>& samples) -> void {
    T castedSamples;
    sampleCaster(offset, groupSize, samples, castedSamples);
    callback(samples, castedSamples);
  };
  if (groupSizes.size() != groupNumber + 1) {
    throw std::exception();
  }
  return alignerCallback;
};
template <unsigned long groupNumber, typename T, typename... other>
AlignerSampleCallback generateAlignerCallback(
    unsigned long offset,
    const std::vector<unsigned long>& groupSizes,
    const std::function<void(const std::vector<StreamSample>&, const T&, const other&...)>&
        callback) {
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  std::function<void(const std::vector<StreamSample>&, const other&...)> callbackReduced =
      [callback, offset, groupSize = groupSizes[groupNumber]](
          const std::vector<StreamSample>& samples, const other&... args) -> void {
    T castedSamples;
    sampleCaster(offset, groupSize, samples, castedSamples);
    callback(samples, castedSamples, args...);
  };
  return generateAlignerCallback<groupNumber + 1>(
      offset + groupSizes[groupNumber], groupSizes, callbackReduced);
};

// Generate Transformer-Aligner Sample Callbacks using Run-time groupings
template <unsigned long groupNumber, typename T>
AlignerSampleCallback generateAlignerCallback(
    Dispatcher* dispatcher,
    unsigned long inputOffset,
    unsigned long outputOffset,
    const std::vector<StreamID>& inputIDs,
    const std::vector<StreamID>& outputIDs,
    const std::vector<unsigned long>& groupSizes,
    const std::function<void(
        const std::vector<StreamID>&,
        const std::vector<StreamSample>&,
        std::vector<StreamSample>&,
        T&)>& callback) {
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  AlignerSampleCallback callbackReduced =
      [dispatcher,
       inputIDs,
       outputIDs,
       callback,
       outputOffset,
       groupSize = groupSizes[groupNumber]](const std::vector<StreamSample>& samplesIn) -> void {
    T castedSamples;
    ResizeAllocHelper<T>::resize(castedSamples, groupSize, dispatcher, outputOffset, outputIDs);
    std::vector<StreamSample> samplesOut(outputIDs.size());
    callback(outputIDs, samplesIn, samplesOut, castedSamples);
    SampleUncaster<T>::uncast(samplesOut, outputOffset, castedSamples);
    for (auto& sampleOut : samplesOut) {
      for (size_t inputIdx = 0; inputIdx < samplesIn.size(); ++inputIdx) {
        sampleOut.metadata->history.emplace(inputIDs[inputIdx], samplesIn[inputIdx].metadata);
      }
    }
    dispatcher->dispatchSamples(samplesOut);
  };
  return callbackReduced;
};
template <unsigned long groupNumber, typename T, typename... other>
AlignerSampleCallback generateAlignerCallback(
    Dispatcher* dispatcher,
    unsigned long inputOffset,
    unsigned long outputOffset,
    const std::vector<StreamID>& inputIDs,
    const std::vector<StreamID>& outputIDs,
    const std::vector<unsigned long>& groupSizes,
    const std::function<void(
        const std::vector<StreamID>&,
        const std::vector<StreamSample>&,
        std::vector<StreamSample>&,
        const T&,
        other&...)>& callback) {
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  std::function<void(
      const std::vector<StreamID>&,
      const std::vector<StreamSample>&,
      std::vector<StreamSample>&,
      other&...)>
      callbackReduced = [callback, inputOffset, groupSize = groupSizes[groupNumber]](
                            const std::vector<StreamID>& _outputIDs,
                            const std::vector<StreamSample>& samplesIn,
                            std::vector<StreamSample>& samplesOut,
                            other&... args) -> void {
    T castedSamples;
    sampleCaster(inputOffset, groupSize, samplesIn, castedSamples);
    callback(_outputIDs, samplesIn, samplesOut, castedSamples, args...);
  };
  return generateAlignerCallback<groupNumber + 1>(
      dispatcher,
      inputOffset + groupSizes[groupNumber],
      outputOffset,
      inputIDs,
      outputIDs,
      groupSizes,
      callbackReduced);
};
template <unsigned long groupNumber, typename T, typename... other>
AlignerSampleCallback generateAlignerCallback(
    Dispatcher* dispatcher,
    unsigned long inputOffset,
    unsigned long outputOffset,
    const std::vector<StreamID>& inputIDs,
    const std::vector<StreamID>& outputIDs,
    const std::vector<unsigned long>& groupSizes,
    const std::function<void(
        const std::vector<StreamID>&,
        const std::vector<StreamSample>&,
        std::vector<StreamSample>&,
        T&,
        other&...)>& callback) {
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  std::function<void(
      const std::vector<StreamID>&,
      const std::vector<StreamSample>&,
      std::vector<StreamSample>&,
      other&...)>
      callbackReduced = [dispatcher, callback, outputOffset, groupSize = groupSizes[groupNumber]](
                            const std::vector<StreamID>& _outputIDs,
                            const std::vector<StreamSample>& samplesIn,
                            std::vector<StreamSample>& samplesOut,
                            other&... args) -> void {
    T castedSamples;
    ResizeAllocHelper<T>::resize(castedSamples, groupSize, dispatcher, outputOffset, _outputIDs);
    callback(_outputIDs, samplesIn, samplesOut, castedSamples, args...);
    SampleUncaster<T>::uncast(samplesOut, outputOffset, castedSamples);
  };
  return generateAlignerCallback<groupNumber + 1>(
      dispatcher,
      inputOffset,
      outputOffset + groupSizes[groupNumber],
      inputIDs,
      outputIDs,
      groupSizes,
      callbackReduced);
};

// Generate Aligner Config Callbacks using Compile-time groupings
// Handle the case of a null config callback
template <unsigned long offset, unsigned long N, typename T>
AlignerConfigCallback generateAlignerConfigCallback(
    const std::function<bool(const std::vector<StreamConfig>&, const T&)>& callback,
    const std::array<bool, N>& skipStreams,
    unsigned long skipOffset = 0) {
  while (skipStreams[offset + skipOffset]) {
    skipOffset++;
    if (skipStreams.size() <= offset + skipOffset) {
      auto str = "Too many configs in Node callback";
      XR_LOGCW("Cthulhu", "{}", str);
      throw std::runtime_error(str);
    }
  }
  AlignerConfigCallback alignerCallback =
      [callback, skipOffset](const std::vector<StreamConfig>& configs) -> bool {
    T castedConfigs;
    configCaster<offset>(configs, castedConfigs, skipOffset);
    return callback(configs, castedConfigs);
  };
  return alignerCallback;
};
template <unsigned long offset, unsigned long N>
AlignerConfigCallback generateAlignerConfigCallback(
    const std::function<bool(const std::vector<StreamConfig>&)>& callback,
    const std::array<bool, N>& skipStreams,
    unsigned long skipOffset = 0) {
  AlignerConfigCallback alignerCallback = [](const std::vector<StreamConfig>& configs) -> bool {
    return false;
  };
  return alignerCallback;
};
template <unsigned long offset, unsigned long N, typename T, typename... other>
AlignerConfigCallback generateAlignerConfigCallback(
    const std::function<bool(const std::vector<StreamConfig>&, const T&, const other&...)>&
        callback,
    const std::array<bool, N>& skipStreams,
    unsigned long skipOffset = 0) {
  while (skipStreams[offset + skipOffset]) {
    skipOffset++;
    if (skipStreams.size() <= offset + skipOffset) {
      auto str = "Too many configs in Node callback";
      XR_LOGCW("Cthulhu", "{}", str);
      throw std::runtime_error(str);
    }
  }
  std::function<bool(const std::vector<StreamConfig>&, const other&...)> callbackReduced =
      [callback, skipOffset](
          const std::vector<StreamConfig>& configs, const other&... args) -> bool {
    T castedConfigs;
    configCaster<offset>(configs, castedConfigs, skipOffset);
    return callback(configs, castedConfigs, args...);
  };
  return generateAlignerConfigCallback<offset + ArraySize<T>::size>(
      callbackReduced, skipStreams, skipOffset);
};

// Generate Aligner Config Callbacks using Run-time groupings
// Handle the case of a null config callback
template <unsigned long groupNumber, typename T>
AlignerConfigCallback generateAlignerConfigCallback(
    unsigned long offset,
    const std::vector<unsigned long>& groupSizes,
    const std::function<bool(const std::vector<StreamConfig>&, const T&)>& callback,
    const std::vector<bool>& skipStreams) {
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  if (skipStreams.size() <= offset) {
    auto str = "Too many configs in Node callback";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  if (skipStreams[offset]) {
    offset += groupSizes[groupNumber];
  }
  AlignerConfigCallback alignerCallback = [callback, offset, groupSize = groupSizes[groupNumber]](
                                              const std::vector<StreamConfig>& configs) -> bool {
    T castedConfigs;
    configCaster(offset, groupSize, configs, castedConfigs);
    return callback(configs, castedConfigs);
  };
  if (groupSizes.size() != groupNumber + 1) {
    throw std::exception();
  }
  return alignerCallback;
};
template <unsigned long groupNumber>
AlignerConfigCallback generateAlignerConfigCallback(
    unsigned long offset,
    const std::vector<unsigned long>& groupSizes,
    const std::function<bool(const std::vector<StreamConfig>&)>& callback,
    const std::vector<bool>& skipStreams) {
  AlignerConfigCallback alignerCallback = [](const std::vector<StreamConfig>& configs) -> bool {
    return false;
  };
  return alignerCallback;
};
template <unsigned long groupNumber, typename T, typename... other>
AlignerConfigCallback generateAlignerConfigCallback(
    unsigned long offset,
    const std::vector<unsigned long>& groupSizes,
    const std::function<bool(const std::vector<StreamConfig>&, const T&, const other&...)>&
        callback,
    const std::vector<bool>& skipStreams) {
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  if (skipStreams.size() <= offset) {
    auto str = "Too many configs in Node callback";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  if (skipStreams[offset]) {
    offset += groupSizes[groupNumber];
  }
  std::function<bool(const std::vector<StreamConfig>&, const other&...)> callbackReduced =
      [callback, offset, groupSize = groupSizes[groupNumber]](
          const std::vector<StreamConfig>& configs, const other&... args) -> bool {
    T castedConfigs;
    configCaster(offset, groupSize, configs, castedConfigs);
    return callback(configs, castedConfigs, args...);
  };
  return generateAlignerConfigCallback<groupNumber + 1>(
      offset + groupSizes[groupNumber], groupSizes, callbackReduced, skipStreams);
};

// Generate Transformer-Aligner Config Callbacks using Run-time groupings
// Handle the case with single input set, no outputs
template <unsigned long groupNumber, typename T>
AlignerConfigCallback generateAlignerConfigCallback(
    Dispatcher* dispatcher,
    unsigned long inputOffset,
    unsigned long outputOffset,
    size_t outSize,
    const std::vector<unsigned long>& groupSizes,
    const std::function<
        bool(const std::vector<StreamConfig>&, std::vector<StreamConfig>&, const T&)>& callback,
    const std::vector<bool>& skipStreams) {
  if (skipStreams.size() <= inputOffset) {
    auto str = "Too many configs in Node callback";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  if (skipStreams[inputOffset]) {
    inputOffset += groupSizes[groupNumber];
  }
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  AlignerConfigCallback callbackReduced =
      [dispatcher, callback, inputOffset, groupSize = groupSizes[groupNumber], outSize](
          const std::vector<StreamConfig>& configsIn) -> bool {
    T castedConfigs;
    configCaster(inputOffset, groupSize, configsIn, castedConfigs);
    std::vector<StreamConfig> configsOut(outSize);
    if (!callback(configsIn, configsOut, castedConfigs)) {
      return false;
    }
    dispatcher->dispatchConfigs(configsOut);
    return true;
  };
  return callbackReduced;
};
// Handle the case of a null config callback
template <unsigned long groupNumber, typename T>
AlignerConfigCallback generateAlignerConfigCallback(
    Dispatcher* dispatcher,
    unsigned long inputOffset,
    unsigned long outputOffset,
    size_t outSize,
    const std::vector<unsigned long>& groupSizes,
    const std::function<bool(const std::vector<StreamConfig>&, std::vector<StreamConfig>&, T&)>&
        callback,
    const std::vector<bool>& skipStreams) {
  if (skipStreams.size() <= outputOffset) {
    auto str = "Too many configs in Node callback";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  if (skipStreams[outputOffset]) {
    outputOffset += groupSizes[groupNumber];
  }
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  AlignerConfigCallback callbackReduced =
      [dispatcher, outSize, callback, outputOffset, groupSize = groupSizes[groupNumber]](
          const std::vector<StreamConfig>& configsIn) -> bool {
    T castedConfigs;
    ResizeHelper<T>::resize(castedConfigs, groupSize);
    std::vector<StreamConfig> configsOut(outSize);
    if (!callback(configsIn, configsOut, castedConfigs)) {
      return false;
    }
    ConfigUncaster<T>::uncast(configsOut, outputOffset, castedConfigs);
    dispatcher->dispatchConfigs(configsOut);
    return true;
  };
  return callbackReduced;
};
template <unsigned long groupNumber, typename T, typename... other>
AlignerConfigCallback generateAlignerConfigCallback(
    Dispatcher* dispatcher,
    unsigned long inputOffset,
    unsigned long outputOffset,
    size_t outSize,
    const std::vector<unsigned long>& groupSizes,
    const std::function<
        bool(const std::vector<StreamConfig>&, std::vector<StreamConfig>&, const T&, other&...)>&
        callback,
    const std::vector<bool>& skipStreams) {
  if (skipStreams.size() <= inputOffset) {
    auto str = "Too many configs in Node callback";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  if (skipStreams[inputOffset]) {
    inputOffset += groupSizes[groupNumber];
  }
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  std::function<bool(const std::vector<StreamConfig>&, std::vector<StreamConfig>&, other&...)>
      callbackReduced = [callback, inputOffset, groupSize = groupSizes[groupNumber]](
                            const std::vector<StreamConfig>& configsIn,
                            std::vector<StreamConfig>& configsOut,
                            other&... args) -> bool {
    T castedConfigs;
    configCaster(inputOffset, groupSize, configsIn, castedConfigs);
    return callback(configsIn, configsOut, castedConfigs, args...);
  };
  return generateAlignerConfigCallback<groupNumber + 1>(
      dispatcher,
      inputOffset + groupSizes[groupNumber],
      outputOffset,
      outSize,
      groupSizes,
      callbackReduced,
      skipStreams);
};
template <unsigned long groupNumber, typename T, typename... other>
AlignerConfigCallback generateAlignerConfigCallback(
    Dispatcher* dispatcher,
    unsigned long inputOffset,
    unsigned long outputOffset,
    size_t outSize,
    const std::vector<unsigned long>& groupSizes,
    const std::function<bool(
        const std::map<StreamIDView, StreamConfig>&,
        std::vector<StreamConfig>&,
        T&,
        other&...)>& callback,
    const std::vector<bool>& skipStreams) {
  if (skipStreams.size() <= outputOffset) {
    auto str = "Too many configs in Node callback";
    XR_LOGCW("Cthulhu", "{}", str);
    throw std::runtime_error(str);
  }
  if (skipStreams[outputOffset]) {
    outputOffset += groupSizes[groupNumber];
  }
  if (groupNumber >= groupSizes.size()) {
    throw std::exception();
  }
  std::function<bool(const std::vector<StreamConfig>&, T&, other&...)> callbackReduced =
      [dispatcher, callback, outputOffset, groupSize = groupSizes[groupNumber]](
          const std::vector<StreamConfig>& configsIn,
          std::vector<StreamConfig>& configsOut,
          other&... args) -> bool {
    T castedConfigs;
    ResizeHelper<T>::resize(castedConfigs, groupSize);
    if (!callback(configsIn, configsOut, castedConfigs, args...)) {
      return false;
    }
    ConfigUncaster<T>::uncast(configsOut, outputOffset, castedConfigs);
    return true;
  };
  return generateAlignerConfigCallback<groupNumber + 1>(
      dispatcher,
      inputOffset,
      outputOffset + groupSizes[groupNumber],
      outSize,
      groupSizes,
      callbackReduced,
      skipStreams);
};
template <unsigned long groupNumber>
AlignerConfigCallback generateAlignerConfigCallback(
    Dispatcher* dispatcher,
    unsigned long inputOffset,
    unsigned long outputOffset,
    size_t outSize,
    const std::vector<unsigned long>& groupSizes,
    const std::function<bool(const std::vector<StreamConfig>&, std::vector<StreamConfig>&)>&
        callback,
    const std::vector<bool>& skipStreams) {
  AlignerConfigCallback callbackReduced = [](const std::vector<StreamConfig>& configsIn) -> bool {
    return false;
  };
  return callbackReduced;
};

inline std::unique_ptr<AlignerBase> alignerFromOptions(
    const AlignerType& type,
    std::unique_ptr<AlignerBase> pointer) {
  switch (type) {
    case AlignerType::SYNC: {
      XR_LOGCW_IF(
          pointer != nullptr,
          "Cthulhu",
          "A custom aligner was supplied, but default SYNC aligner is being used instead!");
      return std::make_unique<Aligner>(1, ThreadPolicy::THREAD_NEUTRAL);
    }
    case AlignerType::ASYNC: {
      XR_LOGCW_IF(
          pointer != nullptr,
          "Cthulhu",
          "A custom aligner was supplied, but default ASYNC aligner is being used instead!");
      return std::make_unique<Aligner>(10, ThreadPolicy::SINGLE_THREADED);
    }
    case AlignerType::CUSTOM:
      // No move necessary, this'll be done automatically by the compiler
      return pointer;
  }
  auto str = "Unhandled aligner type";
  XR_LOGCE("Cthulhu", "{}", str);
  throw std::runtime_error(str);
}

} // namespace details

} // namespace cthulhu
