// Copyright 2004-present Facebook. All Rights Reserved.

#include "TypeRegistryLocal.h"

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

TypeInfoInterfacePtr TypeRegistryLocal::findSampleType(const std::type_index& sampleType) const {
  auto it = sampleTypeMap_.find(sampleType);
  if (it != sampleTypeMap_.end()) {
    return types_.at(it->second);
  }
  return TypeInfoInterfacePtr();
}

TypeInfoInterfacePtr TypeRegistryLocal::findConfigType(const std::type_index& configType) const {
  auto it = configTypeMap_.find(configType);
  if (it != configTypeMap_.end()) {
    return types_.at(it->second);
  }
  return TypeInfoInterfacePtr();
}

TypeInfoInterfacePtr TypeRegistryLocal::findTypeName(const std::string& typeName) const {
  auto it = streamNameMap_.find(typeName);
  if (it != streamNameMap_.end()) {
    return types_.at(it->second);
  }
  return TypeInfoInterfacePtr();
}

TypeInfoInterfacePtr TypeRegistryLocal::findTypeID(uint32_t typeID) const {
  if (typeID > 0 && typeID <= types_.size()) {
    return types_.at(typeID - 1);
  }
  return TypeInfoInterfacePtr();
}

std::vector<std::string> TypeRegistryLocal::typeNames() const {
  std::vector<std::string> typeNames;
  for (const auto& type : streamNameMap_) {
    typeNames.push_back(type.first);
  }
  return typeNames;
}

void TypeRegistryLocal::registerType(TypeDefinition definition) {
  for (const auto& type : types_) {
    if (type->typeName().compare(definition.typeName) == 0) {
      auto str =
          "Attempted to register type: [" + type->typeName() + "] which was detected as duplicate.";
      XR_LOGE("{}", str);
      throw std::runtime_error(str);
    }
  }

  if (definition.sampleType != typeid(nullptr)) {
    sampleTypeMap_[definition.sampleType] = types_.size();
  }
  if (definition.configType && *definition.configType != typeid(nullptr)) {
    configTypeMap_[*definition.configType] = types_.size();
  }
  streamNameMap_[definition.typeName] = types_.size();
  types_.push_back(std::shared_ptr<TypeInfoLocal>(
      new TypeInfoLocal{std::move(definition), static_cast<uint32_t>(types_.size())}));
}

} // namespace cthulhu
