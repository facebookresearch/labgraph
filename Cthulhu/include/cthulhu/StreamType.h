// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/FieldData.h>
#include <cthulhu/StreamInterface.h>
#include <cthulhu/TypeHelpers.h>

#include <array>
#include <memory>
#include <ostream>
#include <string_view>
#include <type_traits>
#include <typeindex>

namespace cthulhu {

class AutoStreamConfig;
class AutoStreamSample;

// These base classes allow data accessors to perform non-const access
// to the underlying data for set functions.
class ConfigAccessor {
 protected:
  StreamConfig& config(AutoStreamConfig* wrapper);
};

class SampleAccessor {
 protected:
  StreamSample& sample(AutoStreamSample* wrapper);
};

class SampleSize : public ConfigAccessor {
 public:
  SampleSize(AutoStreamConfig* wrapper);

  uint32_t get() const;

  operator const uint32_t&() const;

  void set(const uint32_t& value);

  SampleSize& operator=(const uint32_t& value);

  SampleSize(const SampleSize&) = delete;
  SampleSize& operator=(const SampleSize&) = delete;

 private:
  AutoStreamConfig* wrapper_;
};

class AutoStreamConfig {
 public:
  cthulhu::SampleSize sampleSizeInBytes{this};

  // This function will be called to auto-update sampleSizeInBytes every time any field
  // is updated
  virtual uint32_t computeSampleSize() const {
    return 0;
  };

  const StreamConfig& getConfig() const;

  void setConfig(const StreamConfig& config);

  // No copies
  AutoStreamConfig(const AutoStreamConfig& other) = delete;
  AutoStreamConfig& operator=(const AutoStreamConfig& other) = delete;
  AutoStreamConfig(AutoStreamConfig&& other) = delete;
  AutoStreamConfig& operator=(AutoStreamConfig&& other) = delete;

  virtual ~AutoStreamConfig();

 protected:
  // Do not use; construct your AutoStreamConfig subclass instead.
  explicit AutoStreamConfig(size_t staticFieldSize, size_t dynamicFieldSize);
  explicit AutoStreamConfig(const StreamConfig& config);

  StreamConfig config_;
  friend class ConfigAccessor;
};

class AutoStreamSample {
 public:
  AutoStreamSample(const AutoStreamSample& other) = delete;
  AutoStreamSample& operator=(const AutoStreamSample& other) = delete;

  virtual ~AutoStreamSample();

  const StreamSample& getSample() const;

  void setSample(const StreamSample& sample);

 protected:
  // Do not use; construct a AutoStreamSample subclass instead.
  explicit AutoStreamSample(size_t size, size_t numberDynamicFields);
  AutoStreamSample(const StreamSample& sample, size_t size, size_t numberDynamicFields);

  StreamSample sample_;
  friend class SampleAccessor;
};

namespace details {
// Type tag for a POD type in a config field. These are allocated in the parameters block and have
// normal field descriptors
struct pod_type {};
// Type tag for dynamically-sized config field data. These are allocated on the free store,
// accessible by the StreamConfig itself. They're managed behind a RawDynamic.
struct dynamic_type {};

template <class Wrapper>
struct dynamic_parameters;

template <>
struct dynamic_parameters<AutoStreamConfig> {
  static auto get(AutoStreamConfig* wrapper)
      -> decltype(wrapper->getConfig().dynamicParameters.get()) {
    return wrapper->getConfig().dynamicParameters.get();
  }
};

template <>
struct dynamic_parameters<AutoStreamSample> {
  static auto get(AutoStreamSample* wrapper)
      -> decltype(wrapper->getSample().dynamicParameters.get()) {
    return wrapper->getSample().dynamicParameters.get();
  }
};

// The DynamicConfigField is specialized for dynamically-sized types.
// See the specializations below for more information.
template <class FieldType, class Base, class Wrapper>
class DynamicField;

// DynamicFields for strings.
// Inputs: const std::string_view
// Outputs: const std::string_view which reference the underlying memory
template <class Base, class Wrapper>
class DynamicField<std::string, Base, Wrapper> {
 public:
  DynamicField(const std::string& fieldName, Wrapper* wrapper)
      : fieldOffset_(Base::template registerField<std::string>(fieldName, details::dynamic_type())),
        wrapper_(wrapper) {}

  DynamicField& operator=(const DynamicField&) = delete;

  const std::string_view get() const {
    const RawDynamic<>& rawDynamic = *(dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_);
    return rawDynamic.asString();
  }

  size_t size() const {
    const RawDynamic<>& rawDynamic = *(dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_);
    return rawDynamic.size();
  }

  char* ptr() {
    return reinterpret_cast<char*>(
        (dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_)->raw.get());
  }

  void set(const std::string_view str) {
    *(dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_) =
        (str.empty()) ? RawDynamic<>() : RawDynamic<>(str);
  }

  void setPtr(std::shared_ptr<uint8_t>& ptr, size_t count) {
    *(dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_) = RawDynamic<>(ptr, count);
  }

  operator const std::string_view() const {
    return get();
  }

  DynamicField& operator=(const std::string_view str) {
    set(str);
    return *this;
  }

  bool operator==(const DynamicField<std::string, Base, Wrapper>& that) const {
    return (this->get()) == (that.get());
  }

  bool operator!=(const DynamicField<std::string, Base, Wrapper>& that) const {
    return !(this->operator==(that));
  }

 private:
  size_t fieldOffset_;
  Wrapper* wrapper_;
};

// DynamicFields for vectors.
// Inputs: const std::vector<T>&
// Outputs: std::vector<T> which copies the underlying memory
template <class T, class Base, class Wrapper>
class DynamicField<std::vector<T>, Base, Wrapper> {
 public:
  DynamicField(const std::string& fieldName, Wrapper* wrapper)
      : fieldOffset_(
            Base::template registerField<std::vector<T>>(fieldName, details::dynamic_type())),
        wrapper_(wrapper) {}

  DynamicField& operator=(const DynamicField&) = delete;

  std::vector<T> get() const {
    const RawDynamic<>& rawDynamic = *(dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_);
    return rawDynamic.template copyAs<T>();
  }

  size_t size() const {
    const RawDynamic<>& rawDynamic = *(dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_);
    return rawDynamic.size() / sizeof(T);
  }

  T* ptr() {
    return reinterpret_cast<T*>(
        (dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_)->raw.get());
  }

  const T* ptr() const {
    return reinterpret_cast<T*>(
        (dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_)->raw.get());
  }

  void set(const std::vector<T>& vec) {
    *(dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_) =
        (vec.empty()) ? RawDynamic<>() : RawDynamic<>(vec);
  }

  void setPtr(std::shared_ptr<uint8_t>& ptr, size_t count) {
    *(dynamic_parameters<Wrapper>::get(wrapper_) + fieldOffset_) = RawDynamic<>(ptr, count);
  }

  operator std::vector<T>() const {
    return get();
  }

  DynamicField& operator=(const std::vector<T>& vec) {
    set(vec);
    return *this;
  }

  bool operator==(const DynamicField<std::vector<T>, Base, Wrapper>& other) const {
    // Don't compare get()s, since it allocates
    const auto& lhs = *(dynamic_parameters<Wrapper>::get(this->wrapper_) + this->fieldOffset_);
    const auto& rhs = *(dynamic_parameters<Wrapper>::get(other.wrapper_) + other.fieldOffset_);
    return (lhs == rhs);
  }

  bool operator!=(const DynamicField<std::vector<T>, Base, Wrapper>& that) const {
    return !(this->operator==(that));
  }

 private:
  size_t fieldOffset_;
  Wrapper* wrapper_;
};

template <class T>
struct element_of {
  using type = T;
};

template <class T, size_t N>
struct element_of<std::array<T, N>> {
  using type = T;
};

template <class T, size_t N>
struct element_of<T[N]> {
  using type = T;
};

template <class X>
using element_of_t = typename element_of<X>::type;

} // namespace details

template <class Field, class Base>
using DynamicConfigField = details::DynamicField<Field, Base, AutoStreamConfig>;

template <class Field, class Base>
using DynamicSampleField = details::DynamicField<Field, Base, AutoStreamSample>;

template <typename T, class Base>
class ConfigField : public ConfigAccessor {
  static_assert(
      std::is_pod_v<T>,
      "ConfigField only works for POD types; try DynamicConfigField for something fancier");

 public:
  ConfigField(const std::string& fieldName, AutoStreamConfig* wrapper)
      : fieldOffset_(Base::template registerField<T>(fieldName, details::pod_type())),
        wrapper_(wrapper) {}

  const T& get() const {
    return *reinterpret_cast<T*>(wrapper_->getConfig().parameters.get() + fieldOffset_);
  }

  operator const T&() const {
    return get();
  }

  void set(const T& value) {
    *reinterpret_cast<T*>(config(wrapper_).parameters.get() + fieldOffset_) = value;
    config(wrapper_).sampleSizeInBytes = wrapper_->computeSampleSize();
  }

  ConfigField& operator=(const T& value) {
    set(value);
    return *this;
  }

  bool operator==(const ConfigField<T, Base>& that) const {
    return (this->get()) == (that.get());
  }

  bool operator!=(const ConfigField<T, Base>& that) const {
    return !(this->operator==(that));
  }

  details::element_of_t<T>* ptr() {
    return reinterpret_cast<details::element_of_t<T>*>(
        wrapper_->getConfig().parameters.get() + fieldOffset_);
  }

  const details::element_of_t<T>* ptr() const {
    return reinterpret_cast<const details::element_of_t<T>*>(
        wrapper_->getConfig().parameters.get() + fieldOffset_);
  }

 private:
  size_t fieldOffset_;
  AutoStreamConfig* wrapper_;
};

class SampleRate : public ConfigAccessor {
 public:
  SampleRate(AutoStreamConfig* wrapper);

  const double& get() const;

  operator const double&() const;

  void set(const double& value);

  SampleRate& operator=(const double& value);

  SampleRate& operator=(const SampleRate&) = delete;
  SampleRate(const SampleRate&) = delete;

 private:
  AutoStreamConfig* wrapper_;
};

template <class Base>
class ContentBlock;

template <typename T, class Base>
class SampleField : public SampleAccessor {
  static_assert(std::is_pod_v<T>, "SampleField only works for POD types!");

 public:
  SampleField(const std::string& fieldName, AutoStreamSample* wrapper)
      : fieldOffset_(Base::template registerField<T>(fieldName, details::pod_type())),
        wrapper_(wrapper),
        block_(nullptr),
        type_(typeid(T)) {}

  // Overload signals that this sample field resides in a content block
  SampleField(const std::string& fieldName, const ContentBlock<Base>& block)
      : fieldOffset_(Base::template registerField<T>(fieldName, details::pod_type())),
        wrapper_(nullptr),
        block_(&block),
        type_(typeid(T)) {
    Base::samplesInContentBlock();
  }

  const T& get() const {
    return *reinterpret_cast<T*>(accessor(0) + fieldOffset_);
  }

  operator const T&() const {
    return *reinterpret_cast<T*>(accessor(0) + fieldOffset_);
  }

  void set(const T& value) {
    *reinterpret_cast<T*>(accessor(0) + fieldOffset_) = value;
  }

  SampleField& operator=(const T& value) {
    *reinterpret_cast<T*>(accessor(0) + fieldOffset_) = value;
    return *this;
  }

  const T& operator[](size_t idx) const {
    if (!block_)
      throw std::logic_error("Do not use element access for non-SFoCB types");
    else if (idx >= block_->numberSubSamples())
      throw std::out_of_range("SampleField element access out of range");
    return *reinterpret_cast<T*>(accessor(idx) + fieldOffset_);
  }

  T& operator[](size_t idx) {
    if (!block_)
      throw std::logic_error("Do not use element access for non-SFoCB types");
    else if (idx >= block_->numberSubSamples())
      throw std::out_of_range("SampleField element access out of range");
    return *reinterpret_cast<T*>(accessor(idx) + fieldOffset_);
  }

  details::element_of_t<T>* ptr() {
    return reinterpret_cast<details::element_of_t<T>*>(accessor(0) + fieldOffset_);
  }

  const details::element_of_t<T>* ptr() const {
    return reinterpret_cast<const details::element_of_t<T>*>(accessor(0) + fieldOffset_);
  }

 private:
  uint8_t* accessor(size_t batch) const {
    if (block_) {
      return ((CpuBuffer)block_->get()).get() + (batch * Base::getSize());
    } else {
      return wrapper_->getSample().parameters.get();
    }
  }

  size_t fieldOffset_;
  // Pointers are mutually exclusive
  AutoStreamSample* wrapper_ = nullptr;
  const ContentBlock<Base>* block_ = nullptr;
  std::type_index type_;
};

class HeaderTimestamp : public SampleAccessor {
 public:
  HeaderTimestamp(AutoStreamSample* wrapper);

  const double& get() const;

  operator const double&() const;

  void set(const double& value);

  HeaderTimestamp& operator=(const double& value);

  HeaderTimestamp& operator=(const HeaderTimestamp&) = delete;
  HeaderTimestamp(const HeaderTimestamp&) = delete;

 private:
  AutoStreamSample* wrapper_;
};

class HeaderSequence : public SampleAccessor {
 public:
  HeaderSequence(AutoStreamSample* wrapper);

  uint32_t get() const;

  operator const uint32_t&() const;

  void set(const uint32_t& value);

  HeaderSequence& operator=(const uint32_t& value);

  HeaderSequence& operator=(const HeaderSequence&) = delete;
  HeaderSequence(const HeaderSequence&) = delete;

 private:
  AutoStreamSample* wrapper_;
};

class ProcessingTimestamp : public SampleAccessor {
 public:
  ProcessingTimestamp(const std::string& stampName, AutoStreamSample* wrapper);

  const double& get() const;

  operator const double&() const;

  void set(const double& value);

  ProcessingTimestamp& operator=(const double& value);

  ProcessingTimestamp& operator=(const ProcessingTimestamp&) = delete;
  ProcessingTimestamp(const ProcessingTimestamp&) = delete;

 private:
  const std::string stampName_;
  AutoStreamSample* wrapper_;
};

template <class Base>
class ContentBlock : public SampleAccessor {
 public:
  ContentBlock(AutoStreamSample* wrapper) {
    wrapper_ = wrapper;
    Base::registerContent();
  }

  const AnyBuffer& get() const {
    return wrapper_->getSample().payload;
  }

  operator const AnyBuffer&() const {
    return wrapper_->getSample().payload;
  }

  void set(const AnyBuffer& value, uint32_t numberSubSamples = 1) {
    sample(wrapper_).payload = value;
    sample(wrapper_).numberOfSubSamples = numberSubSamples;
  }

  ContentBlock& operator=(const AnyBuffer& value) {
    sample(wrapper_).payload = value;
    return *this;
  }

  const uint32_t& numberSubSamples() const {
    return wrapper_->getSample().numberOfSubSamples;
  }

  void setNumberSubSamples(uint32_t numberSubSamples) {
    sample(wrapper_).numberOfSubSamples = numberSubSamples;
  }

 private:
  AutoStreamSample* wrapper_;
};

template <class Base>
class FieldsBegin {
 public:
  FieldsBegin() {
    if (Base::offsets_.ready) {
      return;
    }
    Base::offsets_.lock.lock();
    if (Base::offsets_.ready) {
      Base::offsets_.lock.unlock();
    }
  }
};

template <class Base>
class FieldsEnd {
 public:
  FieldsEnd() {
    if (Base::offsets_.ready) {
      return;
    }
    Base::offsets_.ready = true;
    Base::offsets_.lock.unlock();
  }
};

class FieldObserver {
 protected:
  template <class Type>
  static FieldData fieldData() {
    return Type::offsets_.data;
  }
  template <class Type>
  bool hasContentBlock() {
    return Type::offsets_.hasContentBlock;
  }
  template <class Type>
  bool hasFieldsInContentBlock() {
    return Type::offsets_.hasSamplesInContentBlock;
  }
};

struct FieldOffsets {
  FieldOffsets() : ready(false), hasContentBlock(false), hasSamplesInContentBlock(false) {}
  std::atomic<bool> ready;
  std::atomic<bool> hasContentBlock;
  std::atomic<bool> hasSamplesInContentBlock;

  std::mutex lock;
  size_t currentOffset = 0;
  size_t currentDynamicOffset = 0;
  FieldData data;
};

#define CTHULHU_AUTOSTREAM_REGISTER_FIELD(Type)                                                 \
  template <typename fieldType>                                                                 \
  static size_t registerField(const std::string& fieldName, ::cthulhu::details::pod_type) {     \
    if (offsets_.ready) {                                                                       \
      return offsets_.data[fieldName].offset;                                                   \
    }                                                                                           \
    offsets_.data[fieldName].isDynamic = false;                                                 \
    offsets_.data[fieldName].offset = offsets_.currentOffset;                                   \
    offsets_.data[fieldName].size = sizeof(fieldType);                                          \
    static_assert(std::is_pod<fieldType>::value, "Cthulhu field must be POD");                  \
    offsets_.data[fieldName].typeName = cthulhu::typeName<fieldType>();                         \
    offsets_.data[fieldName].numElements = cthulhu::typeSize<fieldType>();                      \
    offsets_.currentOffset += sizeof(fieldType);                                                \
    return offsets_.data[fieldName].offset;                                                     \
  };                                                                                            \
                                                                                                \
  template <typename fieldType>                                                                 \
  static size_t registerField(const std::string& fieldName, ::cthulhu::details::dynamic_type) { \
    if (!offsets_.ready) {                                                                      \
      offsets_.data[fieldName].isDynamic = true;                                                \
      offsets_.data[fieldName].offset = offsets_.currentDynamicOffset;                          \
      ++offsets_.currentDynamicOffset;                                                          \
      offsets_.data[fieldName].typeName = cthulhu::typeName<fieldType>();                       \
      offsets_.data[fieldName].size = sizeof(typename fieldType::value_type);                   \
    }                                                                                           \
    return offsets_.data[fieldName].offset;                                                     \
  }                                                                                             \
                                                                                                \
 private:                                                                                       \
  static cthulhu::FieldOffsets offsets_;                                                        \
  friend class cthulhu::FieldsBegin<Type>;                                                      \
  friend class cthulhu::FieldsEnd<Type>;                                                        \
  friend class cthulhu::FieldObserver

#define CTHULHU_AUTOSTREAM_REGISTER_CONTENT(Type) \
  static void registerContent() {                 \
    offsets_.hasContentBlock = true;              \
  }                                               \
  friend class cthulhu::ContentBlock<Type>

#define CTHULHU_AUTOSTREAM_GET_SIZE() \
  static inline size_t getSize() {    \
    return offsets_.currentOffset;    \
  }

#define CTHULHU_AUTOSTREAM_GET_DYNAMIC_FIELD_COUNT() \
  static inline size_t getDynamicFieldCount() {      \
    return offsets_.currentDynamicOffset;            \
  }

#define CTHULHU_AUTOSTREAM_SAMPLES_IN_CONTENT(Type) \
  static void samplesInContentBlock() {             \
    offsets_.hasSamplesInContentBlock = true;       \
  }

#define CTHULHU_AUTOSTREAM_CONFIG(Type)                                                     \
  CTHULHU_AUTOSTREAM_GET_SIZE()                                                             \
  CTHULHU_AUTOSTREAM_GET_DYNAMIC_FIELD_COUNT()                                              \
  Type() : cthulhu::AutoStreamConfig(getSize(), getDynamicFieldCount()) {}                  \
  Type(const cthulhu::StreamConfig& config) : cthulhu::AutoStreamConfig(config) {           \
    config_.sampleSizeInBytes = computeSampleSize();                                        \
  }                                                                                         \
  Type(const Type& other) : Type(other.config_) {}                                          \
  Type& operator=(const Type& other) {                                                      \
    config_ = other.config_;                                                                \
    return *this;                                                                           \
  }                                                                                         \
  Type clone() const {                                                                      \
    auto copy = *this;                                                                      \
    copy.config_ = cthulhu::StreamConfig(getSize(), getDynamicFieldCount());                \
    copy.config_.nominalSampleRate = config_.nominalSampleRate;                             \
    copy.config_.sampleSizeInBytes = config_.sampleSizeInBytes;                             \
    std::memcpy(copy.config_.parameters.get(), config_.parameters.get(), getSize());        \
    for (size_t i = 0; i < getDynamicFieldCount(); ++i) {                                   \
      copy.config_.dynamicParameters.get()[i] = config_.dynamicParameters.get()[i].clone(); \
    }                                                                                       \
    return copy;                                                                            \
  }                                                                                         \
  virtual ~Type() = default;                                                                \
  CTHULHU_AUTOSTREAM_REGISTER_FIELD(Type)

#define CTHULHU_AUTOSTREAM_SAMPLE(Type)                                                       \
  CTHULHU_AUTOSTREAM_GET_SIZE()                                                               \
  CTHULHU_AUTOSTREAM_GET_DYNAMIC_FIELD_COUNT()                                                \
  CTHULHU_AUTOSTREAM_SAMPLES_IN_CONTENT(Type)                                                 \
  explicit Type(bool skipParameters = false)                                                  \
      : cthulhu::AutoStreamSample(skipParameters ? 0U : getSize(), getDynamicFieldCount()) {} \
  Type(const cthulhu::StreamSample& sample, bool skipParameters = false)                      \
      : cthulhu::AutoStreamSample(                                                            \
            sample, skipParameters ? 0U : getSize(), getDynamicFieldCount()) {}               \
  Type(const Type& other) : cthulhu::AutoStreamSample(other.sample_, 0U, 0U) {}               \
  Type& operator=(const Type& other) {                                                        \
    sample_ = other.sample_;                                                                  \
    return *this;                                                                             \
  }                                                                                           \
  virtual ~Type() = default;                                                                  \
  CTHULHU_AUTOSTREAM_REGISTER_FIELD(Type);                                                    \
  CTHULHU_AUTOSTREAM_REGISTER_CONTENT(Type)

} // namespace cthulhu
