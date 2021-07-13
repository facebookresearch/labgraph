// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <fstream>

#include <cthulhu/StreamInterface.h>
#include <cthulhu/StreamType.h>
#include <labgraph/Node.h>

class MyCPPSink : public labgraph::Node {
 public:
  MyCPPSink(const std::string& filename);
  ~MyCPPSink();
  std::vector<std::string> getTopics() const;
  std::vector<labgraph::SubscriberInfo> getSubscribers();
  void mainSubscriber(const cthulhu::StreamSample& sample);

 private:
  std::ofstream outputFile_;
};
