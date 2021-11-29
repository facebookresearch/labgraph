#include <cthulhu/Serialization.h>

namespace cthulhu {

namespace details {
void serializeDynamicFields(
    const SharedRawDynamicArray& dynamicParameters,
    int numDynFields,
    int& offset,
    uint8_t* result) {
  for (int fieldIdx = 0; fieldIdx < numDynFields; ++fieldIdx) {
    // If fieldSize is empty, serialize it anyway. We'll look for the zero when we
    // deserialize to understand if we're supposed to skip a field.
    uint32_t fieldSize = dynamicParameters.get()[fieldIdx].size();
    std::memcpy(result + offset, &fieldSize, sizeof(uint32_t));
    offset += sizeof(uint32_t);
    if (0 != fieldSize) {
      std::memcpy(result + offset, dynamicParameters.get()[fieldIdx].raw.get(), fieldSize);
    }
    offset += fieldSize;
  }
}

void deserializeDynamicFields(
    SharedRawDynamicArray& dynamicParameters,
    int numDynFields,
    int& offset,
    const uint8_t* source) {
  for (int fieldIdx = 0; fieldIdx < numDynFields; ++fieldIdx) {
    uint32_t fieldSize;
    std::memcpy(&fieldSize, &source[0] + offset, sizeof(uint32_t));
    offset += sizeof(uint32_t);
    if (0 != fieldSize) {
      auto& rawDynamic = dynamicParameters.get()[fieldIdx];
      rawDynamic.raw =
          std::shared_ptr<uint8_t>(new uint8_t[fieldSize], [](uint8_t* p) -> void { delete[] p; });
      rawDynamic.elementCount = fieldSize;
      rawDynamic.elementSize = sizeof(uint8_t);
      std::memcpy(rawDynamic.raw.get(), &source[0] + offset, fieldSize);
    }
    offset += fieldSize;
  }
}
} // namespace details

std::vector<uint8_t> serializeConfig(const std::string& typeName, const StreamConfig& config) {
  std::vector<uint8_t> result;
  auto typeInfo = Framework::instance().typeRegistry()->findTypeName(typeName);
  if (!typeInfo) {
    XR_LOGCE("Cthulhu", "Couldn't serialize config, failed to find type in registry: ", typeName);
    return result;
  }
  const auto& paramSize = typeInfo->configParameterSize();
  const auto& numDynFields = typeInfo->configNumberDynamicFields();
  int totalDynSize = 0;
  for (int fieldIdx = 0; fieldIdx < numDynFields; ++fieldIdx) {
    totalDynSize += config.dynamicParameters.get()[fieldIdx].size();
  }
  result.resize(
      paramSize + totalDynSize + sizeof(int) * numDynFields + sizeof(double) + sizeof(uint32_t));
  int offset = 0;
  std::memcpy(&result[0] + offset, config.parameters.get(), paramSize);
  offset += paramSize;

  details::serializeDynamicFields(config.dynamicParameters, numDynFields, offset, result.data());

  std::memcpy(&result[0] + offset, &config.nominalSampleRate, sizeof(double));
  offset += sizeof(double);
  std::memcpy(&result[0] + offset, &config.sampleSizeInBytes, sizeof(uint32_t));
  return result;
}

std::vector<uint8_t> serializeSample(
    const std::string& typeName,
    const StreamSample& sample,
    const StreamConfig* const config) {
  std::vector<uint8_t> result;
  auto typeInfo = Framework::instance().typeRegistry()->findTypeName(typeName);
  if (!typeInfo) {
    XR_LOGCE("Cthulhu", "Couldn't serialize sample, failed to find type in registry: ", typeName);
    return result;
  }
  if (!typeInfo->isBasic()) {
    if (!config) {
      XR_LOGCE(
          "Cthulhu",
          "Couldn't serialize sample for non-basic type without a corresponding config: ",
          typeName);
      return result;
    }
  }
  const auto& paramSize = typeInfo->sampleParameterSize();
  const auto& numDynFields = typeInfo->sampleNumberDynamicFields();
  int totalDynSize = 0;
  for (int fieldIdx = 0; fieldIdx < numDynFields; ++fieldIdx) {
    totalDynSize += sample.dynamicParameters.get()[fieldIdx].size();
  }
  uint32_t payloadSize =
      !typeInfo->isBasic() ? config->sampleSizeInBytes * sample.numberOfSubSamples : 0;
  result.resize(
      paramSize + totalDynSize + sizeof(int) * numDynFields + // numberOfSubSamples per DynField
      payloadSize + sizeof(double) + // timestamp
      2 * sizeof(uint32_t));

  int offset = 0;

  if (sample.parameters) {
    std::memcpy(&result[0] + offset, sample.parameters.get(), paramSize);
    offset += paramSize;
  }

  details::serializeDynamicFields(sample.dynamicParameters, numDynFields, offset, &result[0]);

  std::memcpy(&result[0] + offset, &sample.numberOfSubSamples, sizeof(uint32_t));
  offset += sizeof(uint32_t);
  if (sample.payload) {
    std::memcpy(&result[0] + offset, ((CpuBuffer)sample.payload).get(), payloadSize);
    offset += payloadSize;
  }

  std::memcpy(&result[0] + offset, &sample.metadata->header.timestamp, sizeof(double));
  offset += sizeof(double);
  std::memcpy(&result[0] + offset, &sample.metadata->header.sequenceNumber, sizeof(uint32_t));
  offset += sizeof(uint32_t);
  return result;
}

StreamConfig deserializeConfig(const std::string& typeName, const uint8_t* config) {
  auto typeInfo = Framework::instance().typeRegistry()->findTypeName(typeName);
  if (!typeInfo) {
    XR_LOGCE("Cthulhu", "Couldn't deserialize config, failed to find type in registry: ", typeName);
    return StreamConfig();
  }
  const auto& paramSize = typeInfo->configParameterSize();
  const auto& numDynFields = typeInfo->configNumberDynamicFields();

  StreamConfig result(paramSize, numDynFields);
  int offset = 0;
  std::memcpy(result.parameters.get(), config + offset, paramSize);
  offset += paramSize;
  details::deserializeDynamicFields(result.dynamicParameters, numDynFields, offset, config);
  std::memcpy((void*)&result.nominalSampleRate, config + offset, sizeof(double));
  offset += sizeof(double);
  std::memcpy((void*)&result.sampleSizeInBytes, config + offset, sizeof(uint32_t));
  return result;
}

StreamSample deserializeSample(
    const std::string& typeName,
    const uint8_t* sample,
    const StreamConfig* const config) {
  StreamSample result;
  auto typeInfo = Framework::instance().typeRegistry()->findTypeName(typeName);
  if (!typeInfo) {
    XR_LOGCE("Cthulhu", "Couldn't deserialize sample, failed to find type in registry: ", typeName);
    return result;
  }

  if (!typeInfo->isBasic()) {
    if (!config) {
      XR_LOGCE(
          "Cthulhu",
          "Couldn't deserialize sample for non-basic type without a corresponding config: ",
          typeName);
      return result;
    }
  }

  int offset = 0;

  const auto& paramSize = typeInfo->sampleParameterSize();
  const auto& numDynFields = typeInfo->sampleNumberDynamicFields();
  if (paramSize > 0) {
    result.parameters =
        Framework::instance().memoryPool()->getBufferFromPool(StreamID{""}, paramSize);
    std::memcpy(result.parameters.get(), sample + offset, paramSize);
    offset += paramSize;
  }
  if (numDynFields > 0) {
    result.dynamicParameters = cthulhu::makeSharedRawDynamicArray(numDynFields);
  }

  details::deserializeDynamicFields(result.dynamicParameters, numDynFields, offset, sample);
  std::memcpy((void*)&result.numberOfSubSamples, sample + offset, sizeof(uint32_t));
  offset += sizeof(uint32_t);
  uint32_t payloadSize =
      !typeInfo->isBasic() ? config->sampleSizeInBytes * result.numberOfSubSamples : 0;
  if (payloadSize > 0) {
    result.payload =
        Framework::instance().memoryPool()->getBufferFromPool(StreamID{""}, payloadSize);
    std::memcpy(((CpuBuffer)result.payload).get(), sample + offset, payloadSize);
    offset += payloadSize;
  }

  std::memcpy(&result.metadata->header.timestamp, sample + offset, sizeof(double));
  offset += sizeof(double);
  std::memcpy(&result.metadata->header.sequenceNumber, sample + offset, sizeof(uint32_t));
  offset += sizeof(uint32_t);

  return result;
}

} // namespace cthulhu
