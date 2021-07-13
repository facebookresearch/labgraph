// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <map>
#include <mutex>

#include <cthulhu/StreamRegistryInterface.h>

namespace cthulhu {

class StreamLocal : public StreamInterface {
 public:
  StreamLocal(const StreamDescription& desc);
  virtual ~StreamLocal();

  // Non-copyable. Only one should exist, sitting in the Registry
  StreamLocal(const StreamLocal& other) = delete;
  StreamLocal& operator=(const StreamLocal& other) = delete;

  // Move-constructable, only for insertion into the Registry
  StreamLocal(StreamLocal&& other) : StreamInterface(std::move(other)) {}
  // Non move assignable, shouldn't be needed
  StreamLocal& operator=(StreamLocal&& other) = delete;

 protected:
  virtual bool sendSample(const StreamSample& sample) override;

  virtual bool configure(const StreamConfig& config) override;

  virtual bool hookProducer(const StreamProducer* const producer) override;

  virtual void hookConsumer(const StreamConsumer* const consumer) override;

  virtual void removeProducer(const StreamProducer* const producer) override;

  virtual void removeConsumer(const StreamConsumer* const consumer) override;
};

class StreamRegistryLocal : public StreamRegistryInterface {
 public:
  virtual ~StreamRegistryLocal() = default;

  virtual StreamInterface* registerStream(const StreamDescription& desc) override;

  virtual StreamInterface* getStream(const StreamID& id) override;

  virtual void printStreamInfo() const override;

  virtual std::vector<StreamID> streamsOfTypeID(uint32_t typeID) const override;

 private:
  std::map<const StreamID, StreamLocal> streams_;
  mutable std::mutex streamMutex_;
};

} // namespace cthulhu
