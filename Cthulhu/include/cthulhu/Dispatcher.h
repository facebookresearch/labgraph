// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/StreamInterface.h>

namespace cthulhu {

class Dispatcher {
 public:
  Dispatcher(){};

  virtual ~Dispatcher() = default;

  // Non-copyable
  Dispatcher(const Dispatcher&) = delete;
  Dispatcher& operator=(const Dispatcher&) = delete;

  // Movable
  Dispatcher(Dispatcher&&);
  Dispatcher& operator=(Dispatcher&&);

  void registerProducer(StreamInterface* si);

  void dispatchSamples(const std::vector<StreamSample>& samples);
  void dispatchConfigs(std::vector<StreamConfig>& configs);

  void configureStream(const StreamConfig& config, uint32_t streamNumber);

  const StreamConfig* streamConfig(uint32_t streamNumber);

 protected:
  using IdentifiedProducer = std::pair<StreamIDView, std::unique_ptr<StreamProducer>>;
  std::vector<IdentifiedProducer> producers_;

}; // class Dispatcher

} // namespace cthulhu
