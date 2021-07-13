// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <exception>

namespace labgraph {

template <typename T>
void Node::publish(const std::string& topic, const T& sample) {
  auto topics = getTopics();
  if (std::find(topics.begin(), topics.end(), topic) == topics.end()) {
    throw std::runtime_error("C++ node published to invalid topic '" + topic + "'");
  }
  if (cthulhuPublishersByTopic_.count(topic) == 0) {
    throw std::runtime_error(
        "C++ node tried to publish to topic '" + topic + "' with no bootstrapped Cthulhu stream");
  }

  cthulhuPublishersByTopic_[topic]->publish(sample);
}

} // namespace labgraph
