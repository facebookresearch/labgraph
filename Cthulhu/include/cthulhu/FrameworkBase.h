// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/StreamType.h>

namespace cthulhu {

// On construction, registers a type in the Framework
template <class sampleType, class configType>
class TypeLoader : public FieldObserver {
 public:
  TypeLoader(const std::string& typeName) {
    // Create each type once to register its fields
    sampleType sample;
    configType config;

    TypeDefinition definition;
    definition.typeName = typeName;
    definition.sampleParameterSize = sample.getSize();
    definition.configParameterSize = config.getSize();
    definition.sampleNumberDynamicFields = sample.getDynamicFieldCount();
    definition.configNumberDynamicFields = config.getDynamicFieldCount();
    definition.sampleFields = fieldData<sampleType>();
    definition.configFields = fieldData<configType>();
    definition.hasContentBlock = hasContentBlock<sampleType>();
    definition.hasSamplesInContentBlock = hasFieldsInContentBlock<sampleType>();
    definition.sampleType = typeid(sampleType);
    definition.configType = typeid(configType);

    Framework::instance().typeRegistry()->registerType(std::move(definition));
  };
};

// On construction, registers a type in the Framework w/o a ConfigType
template <class sampleType>
class TypeLoaderBasic : public FieldObserver {
 public:
  TypeLoaderBasic(const std::string& typeName) {
    // Create each type once to register its fields
    sampleType sample;

    TypeDefinition definition;
    definition.typeName = typeName;
    definition.sampleParameterSize = sample.getSize();
    definition.sampleNumberDynamicFields = sample.getDynamicFieldCount();
    definition.sampleFields = fieldData<sampleType>();
    definition.hasContentBlock = hasContentBlock<sampleType>();
    definition.hasSamplesInContentBlock = hasFieldsInContentBlock<sampleType>();
    definition.sampleType = typeid(sampleType);

    Framework::instance().typeRegistry()->registerType(std::move(definition));
  };
};

// On construction, specifies the clock to be used by the framework.
// Before construction, requested clocks will return nullptr.
class ClockAuthority {
 public:
  // Use simTime to specify that simulated time will be used by the Framework.
  // With simulated time, an owning Cthulhu context can and must control the
  // clock.
  ClockAuthority(bool simTime = false, const std::string& owner = "") {
    Framework::instance().clockManager()->setClockAuthority(simTime, owner);
  };
};

} // namespace cthulhu

#define CTHULHU_REGISTER_STREAM_TYPE(typeName, sampleType, configType) \
  cthulhu::FieldOffsets sampleType::offsets_;                          \
  cthulhu::FieldOffsets configType::offsets_;                          \
  cthulhu::TypeLoader<sampleType, configType> typeName(#typeName);

#define CTHULHU_REGISTER_BASIC_STREAM_TYPE(typeName, sampleType) \
  cthulhu::FieldOffsets sampleType::offsets_;                    \
  cthulhu::TypeLoaderBasic<sampleType> typeName(#typeName);
