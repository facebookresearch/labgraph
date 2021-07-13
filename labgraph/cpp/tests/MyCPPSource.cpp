// Copyright 2004-present Facebook. All Rights Reserved.

#include <climits>
#include <thread>

#include "MyCPPSource.h"
#include "TestSample.h"

CTHULHU_REGISTER_BASIC_STREAM_TYPE(Test, TestSample);

std::vector<std::string> MyCPPSource::getTopics() const {
  return {"A"};
}

std::vector<labgraph::PublisherInfo> MyCPPSource::getPublishers() {
  return {{{"A"}, [this]() { mainPublisher(); }}};
}

void MyCPPSource::mainPublisher() {
  // Publisher that sends 10 messages with a single int in each one
  std::this_thread::sleep_for(std::chrono::seconds(1));
  const double publish_sleep = 1.0 / kPublishRate;
  for (uint32_t i = 0; i < kNumSamples; i++) {
    TestSample sample;
    sample.value = i;
    publish<TestSample>("A", sample);
    std::this_thread::sleep_for(std::chrono::duration<double>(publish_sleep));
  }
}
