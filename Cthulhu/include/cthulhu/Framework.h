// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/ClockManagerInterface.h>
#include <cthulhu/ContextRegistryInterface.h>
#include <cthulhu/MemoryPoolInterface.h>
#include <cthulhu/StreamRegistryInterface.h>
#include <cthulhu/TypeRegistryInterface.h>

#include <logging/LogChannel.h>

namespace cthulhu {

struct FrameworkStorage;
class FrameworkInstance;

class Framework {
 public:
  static Framework& instance();

  // Non-copyable
  Framework(const Framework&) = delete;
  Framework& operator=(const Framework&) = delete;

  virtual ~Framework();

  inline void cleanup(bool force = false, bool logging = true) {
    if (force) {
      if (clockManager_) {
        clockManager_->forceClean();
      }
      if (streamRegistry_) {
        streamRegistry_->forceClean();
      }
      if (memoryPool_) {
        memoryPool_->forceClean();
      }
      if (typeRegistry_) {
        typeRegistry_->forceClean();
      }
      if (contextRegistry_) {
        contextRegistry_->forceClean();
      }
    }
    if (!logging) {
      if (clockManager_) {
        clockManager_->disableLogging();
      }
      if (streamRegistry_) {
        streamRegistry_->disableLogging();
      }
      if (memoryPool_) {
        memoryPool_->disableLogging();
      }
      if (typeRegistry_) {
        typeRegistry_->disableLogging();
      }
      if (contextRegistry_) {
        contextRegistry_->disableLogging();
      }
    }
    clockManager_.reset();
    streamRegistry_.reset();
    memoryPool_.reset();
    typeRegistry_.reset();
    contextRegistry_.reset();
  }

  // Destroy the framework without any concern for other Cthulhu users
  //
  // Intended to be used as last-resort cleanup of a misbehaving Cthulhu framework.
  // Users should typically favor cleanup().
  static bool nuke();

  // Throw an exception if the current framework is not valid
  //
  // Mostly internal check run during blocking sequences, but available for use by consumers
  // if desired.
  static void validate();

  inline ClockManagerInterface* clockManager() {
    return clockManager_.get();
  }

  inline MemoryPoolInterface* memoryPool() {
    return memoryPool_.get();
  }

  inline StreamRegistryInterface* streamRegistry() {
    return streamRegistry_.get();
  }

  inline TypeRegistryInterface* typeRegistry() {
    return typeRegistry_.get();
  }

  inline ContextRegistryInterface* contextRegistry() {
    return contextRegistry_.get();
  }

 protected:
  std::shared_ptr<ClockManagerInterface> clockManager_;
  std::shared_ptr<MemoryPoolInterface> memoryPool_;
  std::shared_ptr<StreamRegistryInterface> streamRegistry_;
  std::shared_ptr<TypeRegistryInterface> typeRegistry_;
  std::shared_ptr<ContextRegistryInterface> contextRegistry_;

 private:
  Framework();

  std::unique_ptr<FrameworkStorage> storage_;

  friend class FrameworkInstance;
};

struct FrameworkCleanedUpException : public std::exception {};
struct MemoryPoolInvalidException : public std::exception {};

} // namespace cthulhu

#include <cthulhu/FrameworkBase.h>
