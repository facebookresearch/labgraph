// Copyright 2004-present Facebook. All Rights Reserved.

#include "TypeRegistryIPC.h"

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

TypeRegistryIPC::TypeRegistryIPC(ManagedSHM* shm) : shm_(shm) {
  registryData_ =
      shm_->find_or_construct<TypeRegistryIPCData>("TypeRegistry")(shm_->get_segment_manager());

  if (registryData_ == nullptr) {
    auto str = "Failed to open type registry in shared memory.";
    XR_LOGE("{}", str);
    throw std::runtime_error(str);
  }
  ScopedLockIPC lock(registryData_->registry_lock);
  registryData_->reference_count++;
}

bool TypeRegistryIPC::nuke(ManagedSHM* shm) {
  shm->destroy<TypeRegistryIPCData>("TypeRegistry");
  return true;
}

TypeRegistryIPC::~TypeRegistryIPC() {
  if (registryData_) {
    ScopedLockIPC lock(registryData_->registry_lock);
    registryData_->reference_count--;
    if (registryData_->reference_count == 0 || force_clean_) {
      registryData_->types.clear();
      registryData_->reference_count = 0;
      if (log_enabled_) {
        XR_LOGD("Cleaning up ipc type registry.");
      }
    } else if (log_enabled_) {
      XR_LOGD(
          "Not cleaning ipc type registry, still references: {}", registryData_->reference_count);
    }
  }
}

TypeInfoInterfacePtr TypeRegistryIPC::findSampleType(const std::type_index& sampleType) const {
  auto it = sampleTypeMap_.find(sampleType);
  if (it != sampleTypeMap_.end()) {
    return findTypeName(it->second);
  }
  return TypeInfoInterfacePtr();
}

TypeInfoInterfacePtr TypeRegistryIPC::findConfigType(const std::type_index& configType) const {
  auto it = configTypeMap_.find(configType);
  if (it != configTypeMap_.end()) {
    return findTypeName(it->second);
  }
  return TypeInfoInterfacePtr();
}

TypeInfoInterfacePtr TypeRegistryIPC::findTypeName(
    const std::string& streamName,
    const std::lock_guard<std::mutex>& cacheLock) const {
  // Look in the cache
  auto it = cache_.find(streamName);
  if (it != cache_.end()) {
    return it->second;
  }
  // Check IPC
  TypeNameIPC typeNameIPC(shm_->get_segment_manager());
  typeNameIPC = streamName.c_str();
  ScopedLockIPC lockIPC(registryData_->registry_lock);
  auto ipcData = registryData_->types.find(typeNameIPC);
  if (ipcData != registryData_->types.end()) {
    // Update the local cache
    TypeInfoInterfacePtr result(new TypeInfoIPC(streamName, &ipcData->second));
    cache_[streamName] = result;
    return result;
  }
  return TypeInfoInterfacePtr();
}

TypeInfoInterfacePtr TypeRegistryIPC::findTypeName(const std::string& typeName) const {
  std::lock_guard<std::mutex> lock(cacheMutex_);
  return findTypeName(typeName, lock);
}

TypeInfoInterfacePtr TypeRegistryIPC::findTypeID(uint32_t typeID) const {
  std::lock_guard<std::mutex> lock(cacheMutex_);
  auto it = typeIDMap_.find(typeID);
  if (it != typeIDMap_.end()) {
    return findTypeName(it->second, lock);
  }

  // Check IPC
  TypeNameIPC typeNameIPC(shm_->get_segment_manager());
  ScopedLockIPC lockIPC(registryData_->registry_lock);
  for (auto iter = registryData_->types.cbegin(); iter != registryData_->types.cend(); ++iter) {
    if (typeID == iter->second.typeID) {
      std::string typeName(iter->first.c_str());
      typeIDMap_[typeID] = typeName;
      return findTypeName(typeName, lock);
    }
  }

  return TypeInfoInterfacePtr();
}

std::vector<std::string> TypeRegistryIPC::typeNames() const {
  std::vector<std::string> typeNames;
  ScopedLockIPC lock(registryData_->registry_lock);
  for (auto it = registryData_->types.begin(); it != registryData_->types.end(); ++it) {
    typeNames.push_back(it->first.c_str());
  }
  return typeNames;
}

TypeDefinitionIPC::TypeDefinitionIPC(const TypeDefinition& def, const CharAllocatorIPC& alloc)
    : sampleParameterSize(def.sampleParameterSize),
      configParameterSize(def.configParameterSize),
      sampleNumberDynamicFields(def.sampleNumberDynamicFields),
      configNumberDynamicFields(def.configNumberDynamicFields),
      sampleFields(alloc),
      configFields(alloc),
      hasContentBlock(def.hasContentBlock),
      hasSampleFieldsInContentBlock(def.hasSamplesInContentBlock),
      isBasic(!def.configType) {
  // Caller responsible for supplying sample and config fields separately
}

void TypeRegistryIPC::registerType(TypeDefinition def) {
  uint32_t typeID = 0;
  {
    ScopedLockIPC lock(registryData_->registry_lock);
    TypeNameIPC typeNameIPC(shm_->get_segment_manager());
    typeNameIPC = def.typeName.c_str();
    TypeDefinitionIPC definition(def, shm_->get_segment_manager());
    fieldDataToIPC(shm_->get_segment_manager(), def.sampleFields, definition.sampleFields);
    fieldDataToIPC(shm_->get_segment_manager(), def.configFields, definition.configFields);

    auto it = registryData_->types.find(typeNameIPC);
    if (it != registryData_->types.end()) {
      // Type in shared registry
      definition.typeID = it->second.typeID;
      if (it->second != definition) {
        auto str = "Attempted to register type: [" + def.typeName +
            "] which did not match the existing IPC definition.";
        XR_LOGE("{}", str);
        throw std::runtime_error(str);
      }
    } else {
      // Type is unknown to the shared registry
      definition.typeID = registryData_->types.size() + 1;
      registryData_->types.emplace(typeNameIPC, std::move(definition));
    }
    typeID = definition.typeID;
  }

  if (def.sampleType != typeid(nullptr)) {
    sampleTypeMap_[def.sampleType] = def.typeName;
  }
  if (def.configType && *def.configType != typeid(nullptr)) {
    configTypeMap_[*def.configType] = def.typeName;
  }
  typeIDMap_[typeID] = def.typeName;
}

} // namespace cthulhu
