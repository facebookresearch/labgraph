// Copyright 2004-present Facebook. All Rights Reserved.

#include <fstream>

#include "MyCPPSink.h"
#include "TestSample.h"

MyCPPSink::MyCPPSink(const std::string& filename) {
  outputFile_.open(filename);
}

std::vector<std::string> MyCPPSink::getTopics() const {
  return {"B"};
}

std::vector<labgraph::SubscriberInfo> MyCPPSink::getSubscribers() {
  return {{"B", [this](const cthulhu::StreamSample& sample) { mainSubscriber(sample); }}};
}

void MyCPPSink::mainSubscriber(const cthulhu::StreamSample& sample) {
  // Subscriber that writes messages to disk
  TestSample testSample;
  testSample.setSample(sample);
  outputFile_ << testSample.value << std::endl;
}

MyCPPSink::~MyCPPSink() {
  outputFile_.close();
}
