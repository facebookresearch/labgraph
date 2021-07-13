// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/TypeRegistryInterface.h>

namespace cthulhu {

class TypeRegistryLocal;

class TypeInfoLocal : public TypeInfoInterface {
 public:
  virtual ~TypeInfoLocal() = default;

  virtual inline std::string typeName() const override {
    return definition_.typeName;
  }

  virtual inline uint32_t typeID() const override {
    return typeID_ + 1;
  }

  virtual inline bool isBasic() const override {
    return !(definition_.configType);
  }

  virtual inline size_t sampleParameterSize() const override {
    return definition_.sampleParameterSize;
  }

  virtual inline size_t configParameterSize() const override {
    return definition_.configParameterSize;
  }

  virtual inline size_t sampleNumberDynamicFields() const override {
    return definition_.sampleNumberDynamicFields;
  }

  virtual inline size_t configNumberDynamicFields() const override {
    return definition_.configNumberDynamicFields;
  }

  virtual inline const FieldData& sampleFields() const override {
    return definition_.sampleFields;
  }

  virtual inline const FieldData& configFields() const override {
    return definition_.configFields;
  }

  virtual inline bool hasContentBlock() const override {
    return definition_.hasContentBlock;
  }

  virtual inline bool hasSamplesInContentBlock() const override {
    return definition_.hasSamplesInContentBlock;
  }

 private:
  TypeDefinition definition_;
  uint32_t typeID_ = 0;

  TypeInfoLocal(TypeDefinition definition, uint32_t typeID)
      : definition_(std::move(definition)), typeID_(typeID) {}

  friend class TypeRegistryLocal;
};
using TypeInfoLocalPtr = std::shared_ptr<TypeInfoLocal>;

class TypeRegistryLocal : public TypeRegistryInterface {
 public:
  virtual ~TypeRegistryLocal() = default;

  virtual TypeInfoInterfacePtr findSampleType(const std::type_index& sampleType) const override;
  virtual TypeInfoInterfacePtr findConfigType(const std::type_index& configType) const override;
  virtual TypeInfoInterfacePtr findTypeName(const std::string& streamName) const override;
  virtual TypeInfoInterfacePtr findTypeID(uint32_t typeID) const override;

  virtual std::vector<std::string> typeNames() const override;

  virtual void registerType(TypeDefinition) override;

 private:
  std::vector<TypeInfoLocalPtr> types_;
  std::map<std::type_index, size_t> sampleTypeMap_;
  std::map<std::type_index, size_t> configTypeMap_;
  std::map<std::string, size_t> streamNameMap_;
};

} // namespace cthulhu
