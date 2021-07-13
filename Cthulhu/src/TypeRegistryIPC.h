// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/TypeRegistryInterface.h>

#include "IPCEssentials.h"

#include <boost/interprocess/containers/map.hpp>
#include <boost/interprocess/containers/string.hpp>
#include <boost/interprocess/containers/vector.hpp>

namespace cthulhu {

typedef boost::interprocess::basic_string<char, std::char_traits<char>, CharAllocatorIPC>
    TypeStringIPC;

struct FieldIPC {
  FieldIPC() = delete;
  FieldIPC(const CharAllocatorIPC& alloc) : typeName(alloc), fieldName(alloc) {}
  uint32_t offset;
  uint32_t size;
  TypeStringIPC typeName;
  TypeStringIPC fieldName;
  uint32_t numElements;
  bool isDynamic;
  inline bool operator==(const FieldIPC& other) const {
    return offset == other.offset && size == other.size && typeName == other.typeName &&
        fieldName == other.fieldName && numElements == other.numElements &&
        isDynamic == other.isDynamic;
  }

  inline bool operator!=(const FieldIPC& other) const {
    return !(this->operator==(other));
  }
};

typedef boost::interprocess::allocator<FieldIPC, ManagedSHM::segment_manager>
    FieldIPCVectorAllocType;
typedef boost::interprocess::vector<FieldIPC, FieldIPCVectorAllocType> FieldDataIPC;

inline void fieldDataToIPC(const CharAllocatorIPC& alloc, const FieldData& in, FieldDataIPC& out) {
  for (const auto& field : in) {
    FieldIPC fieldIPC(alloc);
    fieldIPC.offset = field.second.offset;
    fieldIPC.size = field.second.size;
    fieldIPC.typeName = field.second.typeName.c_str();
    fieldIPC.fieldName = field.first.c_str();
    fieldIPC.numElements = field.second.numElements;
    fieldIPC.isDynamic = field.second.isDynamic;
    out.push_back(std::move(fieldIPC));
  }
};

inline void fieldDataFromIPC(const FieldDataIPC& in, FieldData& out) {
  for (const auto& fieldIPC : in) {
    Field field;
    field.offset = fieldIPC.offset;
    field.size = fieldIPC.size;
    field.typeName = fieldIPC.typeName.c_str();
    field.numElements = fieldIPC.numElements;
    field.isDynamic = fieldIPC.isDynamic;
    out[fieldIPC.fieldName.c_str()] = std::move(field);
  }
};

struct TypeDefinitionIPC {
  TypeDefinitionIPC() = delete;
  TypeDefinitionIPC(const TypeDefinition&, const CharAllocatorIPC& alloc);
  uint32_t typeID;
  uint32_t sampleParameterSize;
  uint32_t configParameterSize;
  uint32_t sampleNumberDynamicFields;
  uint32_t configNumberDynamicFields;
  FieldDataIPC sampleFields;
  FieldDataIPC configFields;
  bool hasContentBlock;
  bool hasSampleFieldsInContentBlock;
  bool isBasic;

  inline bool operator==(const TypeDefinitionIPC& other) const {
    bool match = (sampleParameterSize == other.sampleParameterSize) &&
        (configParameterSize == other.configParameterSize) &&
        (sampleNumberDynamicFields == other.sampleNumberDynamicFields) &&
        (configNumberDynamicFields == other.configNumberDynamicFields) &&
        (sampleFields.size() == other.sampleFields.size()) &&
        (configFields.size() == other.configFields.size()) &&
        (hasContentBlock == other.hasContentBlock) && (isBasic == other.isBasic) &&
        (hasSampleFieldsInContentBlock == other.hasSampleFieldsInContentBlock) &&
        (typeID == other.typeID);
    if (!match) {
      return false;
    }
    for (size_t i = 0; i < sampleFields.size() && match; i++) {
      match &= sampleFields[i] == other.sampleFields[i];
    }
    for (size_t i = 0; i < configFields.size() && match; i++) {
      match &= configFields[i] == other.configFields[i];
    }
    return match;
  }

  inline bool operator!=(const TypeDefinitionIPC& other) const {
    return !(this->operator==(other));
  }
};

class TypeRegistryIPC;

class TypeInfoIPC : public TypeInfoInterface {
 public:
  virtual ~TypeInfoIPC() = default;

  virtual inline std::string typeName() const override {
    return name_;
  }

  virtual inline uint32_t typeID() const override {
    return definition_->typeID;
  }

  virtual inline bool isBasic() const override {
    return definition_->isBasic;
  }

  virtual inline size_t sampleParameterSize() const override {
    return definition_->sampleParameterSize;
  }

  virtual inline size_t configParameterSize() const override {
    return definition_->configParameterSize;
  }

  virtual inline size_t sampleNumberDynamicFields() const override {
    return definition_->sampleNumberDynamicFields;
  }

  virtual inline size_t configNumberDynamicFields() const override {
    return definition_->configNumberDynamicFields;
  }

  virtual inline const FieldData& sampleFields() const override {
    return sampleFields_;
  }

  virtual inline const FieldData& configFields() const override {
    return configFields_;
  }

  virtual inline bool hasContentBlock() const override {
    return definition_->hasContentBlock;
  }

  virtual inline bool hasSamplesInContentBlock() const override {
    return definition_->hasSampleFieldsInContentBlock;
  }

 private:
  TypeInfoIPC(std::string name, TypeDefinitionIPC* definition)
      : name_(name), definition_(definition) {
    fieldDataFromIPC(definition_->configFields, configFields_);
    fieldDataFromIPC(definition_->sampleFields, sampleFields_);
  }

  std::string name_;
  TypeDefinitionIPC* definition_;
  FieldData configFields_;
  FieldData sampleFields_;

  friend class TypeRegistryIPC;
};
using TypeInfoIPCPtr = std::shared_ptr<TypeInfoIPC>;

typedef boost::interprocess::basic_string<char, std::char_traits<char>, CharAllocatorIPC>
    TypeNameIPC;

struct TypeRegistryIPCData {
  typedef boost::interprocess::
      allocator<std::pair<const TypeNameIPC, TypeDefinitionIPC>, ManagedSHM::segment_manager>
          MapAllocType;
  typedef boost::interprocess::
      map<TypeNameIPC, TypeDefinitionIPC, std::less<TypeNameIPC>, MapAllocType>
          MapType;

  TypeRegistryIPCData() = delete;
  TypeRegistryIPCData(const TypeRegistryIPCData&) = delete;
  TypeRegistryIPCData(TypeRegistryIPCData&&) = delete;

  TypeRegistryIPCData(const MapAllocType& alloc) : types(std::less<TypeNameIPC>(), alloc) {}

  MapType types;
  MutexIPC registry_lock;

  // Maintain a count of processes using the registry.
  // When this reaches 0, the process should cleanup the map
  uint32_t reference_count = 0;
};

class TypeRegistryIPC : public TypeRegistryInterface {
 public:
  TypeRegistryIPC(ManagedSHM* shm);
  virtual ~TypeRegistryIPC();

  virtual TypeInfoInterfacePtr findSampleType(const std::type_index& sampleType) const override;
  virtual TypeInfoInterfacePtr findConfigType(const std::type_index& configType) const override;
  virtual TypeInfoInterfacePtr findTypeName(const std::string& typeName) const override;
  virtual TypeInfoInterfacePtr findTypeID(uint32_t typeID) const override;

  virtual std::vector<std::string> typeNames() const override;

  virtual void registerType(TypeDefinition) override;

  // Destroy the framework without any concern for other Cthulhu users
  //
  // Intended to be used as last-resort cleanup of a misbehaving Cthulhu framework.
  // Users should typically favor cleanup().
  static bool nuke(ManagedSHM* shm);

 private:
  TypeRegistryIPCData* registryData_ = nullptr;
  ManagedSHM* shm_;

  // Cache the results in local memory so we don't have to go back to shared every time
  // and the underlying types don't change (new types can be added, but never modified)
  mutable std::unordered_map<std::string, TypeInfoInterfacePtr> cache_;
  mutable std::map<uint32_t, std::string> typeIDMap_;
  mutable std::mutex cacheMutex_;

  // These maps will no be modified after type initialization.
  std::map<std::type_index, std::string> sampleTypeMap_;
  std::map<std::type_index, std::string> configTypeMap_;

  TypeInfoInterfacePtr findTypeName(const std::string& typeName, const std::lock_guard<std::mutex>&)
      const;
};

} // namespace cthulhu
