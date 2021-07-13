// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/Framework.h>
#include <cthulhu/StreamInterface.h>

#include <sstream>

#include <boost/crc.hpp>

#include <logging/LogChannel.h>

namespace cthulhu {

namespace details {
void serializeDynamicFields(
    const SharedRawDynamicArray& dynamicParameters,
    int numDynFields,
    int& offset,
    uint8_t* result);

void deserializeDynamicFields(
    SharedRawDynamicArray& dynamicParameters,
    int numDynFields,
    int& offset,
    const uint8_t* source);
} // namespace details

/**
 *  Compute a checksum for a type definition, based on its sample type.
 *  The checksum can be used to validate across processes/machines that the
 *  layout for a given type matches.
 *  Returns -1 on failure, otherwise returns the checksum.
 */
template <class SampleType>
int typeChecksum() {
  auto sampleTypeInfo = Framework::instance().typeRegistry()->findSampleType(typeid(SampleType));
  if (!sampleTypeInfo) {
    XR_LOGCE(
        "Cthulhu",
        "Couldn't compute checksum for type info, failed to find sample type in registry: ",
        typeid(SampleType).name());
    return -1;
  }

  std::stringstream ss;
  ss << sampleTypeInfo->typeName();
  ss << sampleTypeInfo->isBasic();
  ss << sampleTypeInfo->hasContentBlock();
  ss << sampleTypeInfo->hasSamplesInContentBlock();

  auto addFields = [&ss](const FieldData& fields) -> void {
    for (const auto& field : fields) {
      ss << field.first;
      ss << field.second.offset;
      ss << field.second.size;
      ss << field.second.typeName;
      ss << field.second.numElements;
      ss << field.second.isDynamic;
    }
  };

  addFields(sampleTypeInfo->configFields());
  addFields(sampleTypeInfo->sampleFields());

  boost::crc_32_type result;
  result.process_bytes(ss.str().data(), ss.str().length());

  return result.checksum();
}

/**
 *  Serialize a Stream Config into a flat array of bytes
 */
std::vector<uint8_t> serializeConfig(const std::string& typeName, const StreamConfig& config);

/**
 *  Serialize a Stream Config into a flat array of bytes
 */
template <class ConfigType>
std::vector<uint8_t> serializeConfig(const ConfigType& config) {
  auto typeInfo = Framework::instance().typeRegistry()->findConfigType(typeid(ConfigType));
  if (!typeInfo) {
    XR_LOGCE(
        "Cthulhu",
        "Couldn't serialize config, failed to find type in registry: ",
        typeid(ConfigType).name());
    return std::vector<uint8_t>{};
  }

  return serializeConfig(typeInfo->typeName(), config.getConfig());
}

/**
 *  Deserialize a Stream Config from a flat array of bytes
 */
StreamConfig deserializeConfig(const std::string& typeName, const uint8_t* config);

inline StreamConfig deserializeConfig(
    const std::string& typeName,
    const std::vector<uint8_t>& config) {
  return deserializeConfig(typeName, config.data());
}

/**
 *  Deserialize a Stream Config from a flat array of bytes
 */
template <class ConfigType>
ConfigType deserializeConfig(const std::vector<uint8_t>& config) {
  auto typeInfo = Framework::instance().typeRegistry()->findConfigType(typeid(ConfigType));
  if (!typeInfo) {
    XR_LOGCE(
        "Cthulhu",
        "Couldn't deserialize config, failed to find type in registry: ",
        typeid(ConfigType).name());
    return ConfigType();
  }

  return deserializeConfig(typeInfo->typeName(), config);
}

/**
 *  Serialize a Stream Sample into a flat array of bytes, using the current Config for non-basic
 * streams.
 */
std::vector<uint8_t> serializeSample(
    const std::string& typeName,
    const StreamSample& sample,
    const StreamConfig* const config = nullptr);

/**
 *  Serialize a Stream Sample into a flat array of bytes, using the current Config for non-basic
 * streams.
 */
template <class SampleType, class ConfigType = void>
std::vector<uint8_t> serializeSample(
    const SampleType& sample,
    const ConfigType* const config = nullptr) {
  std::vector<uint8_t> result;
  auto typeInfo = Framework::instance().typeRegistry()->findSampleType(typeid(SampleType));
  if (!typeInfo) {
    XR_LOGCE(
        "Cthulhu",
        "Couldn't serialize sample, failed to find type in registry: ",
        typeid(SampleType).name());
    return result;
  }

  if (!typeInfo->isBasic()) {
    if (!config) {
      XR_LOGCE(
          "Cthulhu",
          "Couldn't serialize sample for non-basic type without a corresponding config: ",
          typeid(SampleType).name());
      return result;
    }
    auto configTypeInfo = Framework::instance().typeRegistry()->findConfigType(typeid(ConfigType));
    if (configTypeInfo != typeInfo) {
      XR_LOGCE(
          "Cthulhu",
          "Couldn't serialize sample for with non-matching config. Sample type was: ",
          typeid(SampleType).name());
      return result;
    }
  }

  const StreamConfig* streamConfigPtr = nullptr;
  if constexpr (!std::is_same_v<void, ConfigType>) {
    streamConfigPtr = (config ? &config->getConfig() : nullptr);
  }
  return serializeSample(typeInfo->typeName(), sample.getSample(), streamConfigPtr);
}

/**
 *  Deserialize a Stream Sample from a flat array of bytes, using the current Config for non-basic
 * streams.
 */
StreamSample deserializeSample(
    const std::string& typeName,
    const uint8_t* sample,
    const StreamConfig* const config = nullptr);

inline StreamSample deserializeSample(
    const std::string& typeName,
    const std::vector<uint8_t>& sample,
    const StreamConfig* const config = nullptr) {
  return deserializeSample(typeName, sample.data(), config);
}

/**
 *  Deserialize a Stream Sample from a flat array of bytes, using the current Config for non-basic
 * streams.
 */
template <class SampleType, class ConfigType = void>
SampleType deserializeSample(
    const std::vector<uint8_t>& sample,
    const ConfigType* const config = nullptr) {
  SampleType result;
  auto typeInfo = Framework::instance().typeRegistry()->findSampleType(typeid(SampleType));
  if (!typeInfo) {
    XR_LOGCE(
        "Cthulhu",
        "Couldn't deserialize sample, failed to find type in registry: ",
        typeid(SampleType).name());
    return result;
  }

  if (!typeInfo->isBasic()) {
    auto configTypeInfo = Framework::instance().typeRegistry()->findConfigType(typeid(ConfigType));
    if (configTypeInfo != typeInfo) {
      XR_LOGCE(
          "Cthulhu",
          "Couldn't deserialize sample for with non-matching config. Sample type was: ",
          typeid(SampleType).name());
      return result;
    }
  }

  const StreamConfig* streamConfigPtr = nullptr;
  if constexpr (!std::is_same_v<void, ConfigType>) {
    streamConfigPtr = (config ? &config->getConfig() : nullptr);
  }

  return deserializeSample(typeInfo->typeName(), sample, streamConfigPtr);
}

} // namespace cthulhu
