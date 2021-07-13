// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <labgraph/Node.h>

class MyCPPSource : public labgraph::Node {
 public:
  std::vector<std::string> getTopics() const;
  std::vector<labgraph::PublisherInfo> getPublishers();
  void mainPublisher();

  static constexpr int const& kNumSamples = 10;
  static constexpr double const& kPublishRate = 5.0;
};
