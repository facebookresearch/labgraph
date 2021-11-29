// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/Framework.h>

// IPC Hybrid Targets
#include "ClockManagerIPC.h"
#include "ContextRegistryIPC.h"
#include "MemoryPoolIPCHybrid.h"
#include "StreamRegistryIPCHybrid.h"
#include "TypeRegistryIPC.h"

// Local targets
#include "ClockManagerLocal.h"
#include "ContextRegistryLocal.h"
#include "MemoryPoolLocal.h"
#include "StreamRegistryLocal.h"
#include "TypeRegistryLocal.h"

#include <cstdlib>

#ifdef _WIN32
#define DLLIMPORT __declspec(dllimport)
#else
#define DLLIMPORT
#endif

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

const static char* DEFAULT_SHM_NAME = "CthulhuSHM";
const static char* SHM_NAME_ENV_VAR = "CTHULHU_SHM_NAME";

const static char* DISABLE_SHARED_MEMORY_ENV_VAR = "CTHULHU_DISABLE_SHARED_MEMORY";
const static char* ENABLE_AUDITOR_ENV_VAR = "CTHULHU_ENABLE_AUDITOR";

static std::string shm_name() {
  return std::getenv(SHM_NAME_ENV_VAR) ? std::getenv(SHM_NAME_ENV_VAR) : DEFAULT_SHM_NAME;
}

extern DLLIMPORT Framework* getFramework();

struct FrameworkStorage {
  FrameworkStorage()
      : shmName(shm_name()),
        sharedMemory(boost::interprocess::open_or_create, shmName.c_str(), shmSize) {
    if (std::strcmp(shmName.c_str(), DEFAULT_SHM_NAME) != 0) {
      XR_LOGD("Using non-default shared memory name: {}", shmName);
    } else {
      XR_LOGD("Using default shared memory name: {}", shmName);
    }
  }
  const std::string shmName;
  const size_t shmSize = 500 * 1024 * 1024;
  const size_t shmGPUSize = 500 * 1024 * 1024;
  ManagedSHM sharedMemory;
};

Framework& Framework::instance() {
  return *getFramework();
}

Framework::Framework() : storage_(nullptr) {
  if (!std::getenv(DISABLE_SHARED_MEMORY_ENV_VAR)) {
    bool enableAuditor = std::getenv(ENABLE_AUDITOR_ENV_VAR) != nullptr;
    bool memoryValid = false;
    // so that we're not destroying vulkan connect in between
    std::shared_ptr<VulkanUtil> vulkanUtil = std::make_shared<VulkanUtil>();
    while (!memoryValid) {
      storage_.reset(new FrameworkStorage());
      memoryPool_ = std::make_unique<MemoryPoolIPCHybrid>(
          &storage_->sharedMemory,
          storage_->shmSize,
          storage_->shmGPUSize,
          vulkanUtil,
          enableAuditor);
      if (memoryPool_->isValid()) {
        memoryValid = true;
      } else {
        // we must destroy the pool before nuking to prevent segfaults in destruction
        memoryPool_.reset();
        nuke();
      }
    }
    clockManager_ = std::make_unique<ClockManagerIPC>(&storage_->sharedMemory);
    contextRegistry_ = std::make_unique<ContextRegistryIPC>(&storage_->sharedMemory);
    typeRegistry_ = std::make_unique<TypeRegistryIPC>(&storage_->sharedMemory);
    streamRegistry_ = std::make_unique<StreamRegistryIPCHybrid>(
        dynamic_cast<MemoryPoolIPCHybrid*>(memoryPool_.get()),
        typeRegistry_.get(),
        &storage_->sharedMemory);
  } else {
    memoryPool_ = std::make_unique<MemoryPoolLocal>();
    clockManager_ = std::make_unique<ClockManagerLocal>();
    typeRegistry_ = std::make_unique<TypeRegistryLocal>();
    streamRegistry_ = std::make_unique<StreamRegistryLocal>();
    contextRegistry_ = std::make_unique<ContextRegistryLocal>();
  }
}

bool Framework::nuke() {
#if !defined(_WIN32) && !defined(__ANDROID__)
  std::string name(shm_name());
  if (!boost::interprocess::shared_memory_object::remove(name.c_str())) {
    try {
      boost::interprocess::shared_memory_object exists(
          boost::interprocess::open_only, name.c_str(), boost::interprocess::read_only);
    } catch (boost::interprocess::interprocess_exception e) {
      return e.get_error_code() == boost::interprocess::not_found_error;
    }
    return false; // this can only succeed if the section still exists
  }
  return true;
#else
  FrameworkStorage storage;
  return StreamRegistryIPCHybrid::nuke(&storage.sharedMemory) &&
      TypeRegistryIPC::nuke(&storage.sharedMemory) &&
      ContextRegistryIPC::nuke(&storage.sharedMemory) &&
      ClockManagerIPC::nuke(&storage.sharedMemory) &&
      MemoryPoolIPCHybrid::nuke(&storage.sharedMemory);
#endif
}

void Framework::validate() {
  auto memoryPool = Framework::instance().memoryPool();
  if (memoryPool != nullptr && !Framework::instance().memoryPool()->isValid()) {
    throw std::runtime_error("Framework is not valid");
  }
}

Framework::~Framework() {
  cleanup(false, false);
}

} // namespace cthulhu
