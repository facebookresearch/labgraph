// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <optional>
#include <string>
#include <typeindex>

#include <cthulhu/FieldData.h>
#include <cthulhu/ForceCleanable.h>
#include <cthulhu/LogDisabling.h>
#include <cthulhu/StreamInterface.h>

namespace cthulhu {

class TypeInfoInterface {
 public:
  virtual ~TypeInfoInterface() = default;

  virtual std::string typeName() const = 0;
  virtual uint32_t typeID() const = 0;
  virtual bool isBasic() const = 0;
  virtual size_t sampleParameterSize() const = 0;
  virtual size_t configParameterSize() const = 0;
  virtual size_t sampleNumberDynamicFields() const = 0;
  virtual size_t configNumberDynamicFields() const = 0;
  virtual const FieldData& sampleFields() const = 0;
  virtual const FieldData& configFields() const = 0;
  virtual bool hasContentBlock() const = 0;
  virtual bool hasSamplesInContentBlock() const = 0;
};
using TypeInfoInterfacePtr = std::shared_ptr<TypeInfoInterface>;

struct TypeDefinition {
  std::string typeName;
  std::type_index sampleType = typeid(nullptr);
  std::optional<std::type_index> configType = std::nullopt;
  size_t sampleParameterSize = 0;
  size_t configParameterSize = 0;
  size_t sampleNumberDynamicFields = 0;
  size_t configNumberDynamicFields = 0;
  FieldData sampleFields;
  FieldData configFields;
  bool hasContentBlock = false;
  bool hasSamplesInContentBlock = false;
};

class TypeRegistryInterface : public ForceCleanable, public LogDisabling {
 public:
  virtual ~TypeRegistryInterface() = default;

  virtual TypeInfoInterfacePtr findSampleType(const std::type_index& sampleType) const = 0;
  virtual TypeInfoInterfacePtr findConfigType(const std::type_index& configType) const = 0;
  virtual TypeInfoInterfacePtr findTypeName(const std::string& typeName) const = 0;
  virtual TypeInfoInterfacePtr findTypeID(uint32_t typeID) const = 0;

  virtual std::vector<std::string> typeNames() const = 0;

  inline bool isValidStreamType(
      const std::type_index& sampleType,
      const std::type_index& configType) const {
    if (!findConfigType(configType) || !findSampleType(sampleType)) {
      return false;
    }
    return findSampleType(sampleType)->typeID() == findConfigType(configType)->typeID();
  };

  virtual void registerType(TypeDefinition) = 0;
};

} // namespace cthulhu
