// Copyright 2004-present Facebook. All Rights Reserved.

#include "StreamRegistryLocal.h"

#include <cthulhu/Framework.h>

#include <algorithm>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

StreamLocal::StreamLocal(const StreamDescription& desc) : StreamInterface(desc) {}

StreamLocal::~StreamLocal() = default;

bool StreamLocal::sendSample(const StreamSample& sample) {
  if (paused_) {
    return true;
  }

  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  for (const auto& consumer : consumers_) {
    consumer->consumeSample(sample);
  }

  return true;
};

bool StreamLocal::configure(const StreamConfig& config) {
  configured_ = true;
  // TBD: compare the configs to see if this is an update
  config_ = config;
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  for (const auto& consumer : consumers_) {
    consumer->receiveConfig(config_);
  }

  return true;
};

bool StreamLocal::hookProducer(const StreamProducer* const producer) {
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  if (producer_ != nullptr) {
    XR_LOGD("Not hooking producer on stream: {}", description_.id());
    return false;
  }
  XR_LOGD("Hooking producer on stream: {}", description_.id());
  producer_ = producer;
  return true;
};

void StreamLocal::hookConsumer(const StreamConsumer* const consumer) {
  XR_LOGD("Hooking consumer on stream: {}", description_.id());
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  consumers_.push_back(consumer);
  // If this is a basic stream, none of the downstream consumers are expecting to use
  // the config, but we still need to produce the signal
  if (isConfigured() ||
      Framework::instance().typeRegistry()->findTypeID(description_.type())->isBasic()) {
    consumer->receiveConfig(config_);
  }
};

void StreamLocal::removeProducer(const StreamProducer* const producer) {
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  if (producer_ == producer) {
    XR_LOGD("Removing producer on stream: {}", description_.id());
    producer_ = nullptr;
  } else {
    XR_LOGD("Not removing producer on stream: {}", description_.id());
  }
};

void StreamLocal::removeConsumer(const StreamConsumer* const consumer) {
  std::lock_guard<std::timed_mutex> lock(timed_mutex_);
  auto it = std::find(consumers_.begin(), consumers_.end(), consumer);
  if (it != consumers_.end()) {
    XR_LOGD("Removing consumer on stream: {}", description_.id());
    consumers_.erase(it);
  }
};

StreamInterface* StreamRegistryLocal::registerStream(const StreamDescription& desc) {
  std::lock_guard<std::mutex> lock(streamMutex_);
  auto s = streams_.find(desc.id());
  if (s != streams_.end()) {
    return static_cast<StreamInterface*>(&(s->second));
  }
  XR_LOGD("Inserting stream: {} into registry.", desc.id());
  streams_.insert(std::make_pair(desc.id(), StreamLocal(desc)));
  return static_cast<StreamInterface*>(&(streams_.find(desc.id())->second));
}

StreamInterface* StreamRegistryLocal::getStream(const StreamID& id) {
  std::lock_guard<std::mutex> lock(streamMutex_);
  auto s = streams_.find(id);
  if (s != streams_.end()) {
    return static_cast<StreamInterface*>(&(s->second));
  }
  XR_LOGW(
      "Requested a stream from the registry that does not exist, and insertion is not allowed.");
  return nullptr;
}

void StreamRegistryLocal::printStreamInfo() const {
  std::lock_guard<std::mutex> lock(streamMutex_);
  for (const auto& stream : streams_) {
    XR_LOGD("{}: ", stream.first);
    XR_LOGD(" - Producer: {}", (stream.second.producer() != nullptr ? "ON" : "OFF"));
    XR_LOGD(" - Consumers: {}", stream.second.consumers().size());
  }
};

std::vector<StreamID> StreamRegistryLocal::streamsOfTypeID(uint32_t typeID) const {
  std::vector<StreamID> ids;

  if (typeID == 0) {
    return ids;
  }

  std::lock_guard<std::mutex> lock(streamMutex_);
  for (const auto& stream : streams_) {
    if (stream.second.description().type() == typeID) {
      ids.push_back(stream.second.description().id());
    }
  }
  return ids;
};

} // namespace cthulhu
