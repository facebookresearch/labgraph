// Copyright 2004-present Facebook. All Rights Reserved.

#include <algorithm>
#include <cassert>
#include <map>
#include <thread>
#include <vector>

#include <cthulhu/Framework.h>
#include <cthulhu/StreamInterface.h>
#include <labgraph/Node.h>
#include <pybind11/pybind11.h>

namespace labgraph {

Node::Node() : context_("") {}

void Node::run() {
  pybind11::gil_scoped_release release;
  std::vector<std::thread> threads;
  auto publishers = getPublishers();
  for (const auto& publisherInfo : publishers) {
    threads.push_back(std::thread(publisherInfo.publisher));
  }
  for (auto& thread : threads) {
    thread.join();
  }
}

void Node::bootstrap(NodeBootstrapInfo& bootstrapInfo) {
  for (const auto& topic : bootstrapInfo.topics) {
    bootstrapStream(topic.topicName, topic.streamID);
  }
}

void Node::bootstrapStream(const std::string& topic, const cthulhu::StreamID& streamID) {
  auto topics = getTopics();
  if (std::find(topics.begin(), topics.end(), topic) == topics.end()) {
    throw std::runtime_error("C++ node bootstrapped with invalid topic '" + topic + "'");
  }
  if (streamIDsByTopic_.count(topic) != 0) {
    throw std::runtime_error("C++ node bootstrapped topic '" + topic + "' multiple times");
  }
  streamIDsByTopic_[topic] = streamID;

  auto labgraphPublishers = getPublishers();
  auto labgraphSubscribers = getSubscribers();
  auto labgraphTransformers = getTransformers();

  cthulhu::StreamInterface* si =
      cthulhu::Framework::instance().streamRegistry()->getStream(streamID);
  if (!si) {
    throw std::runtime_error(
        "C++ node bootstrapped topic '" + topic + "' with invalid stream ID '" + streamID + "'");
  }
  cthulhu::StreamDescription desc = si->description();

  for (const auto& publisher : labgraphPublishers) {
    auto topicsBegin = publisher.publishedTopics.begin();
    auto topicsEnd = publisher.publishedTopics.end();
    if (std::find(topicsBegin, topicsEnd, topic) != topicsEnd) {
      auto cthulhuType = cthulhu::Framework::instance().typeRegistry()->findTypeID(desc.type());
      cthulhuPublishersByTopic_[topic] =
          cthulhu::ptrWrap(context_.advertise(desc.id(), desc.type()));
      break;
    }
  }

  for (const auto& subscriber : labgraphSubscribers) {
    if (subscriber.subscribedTopic == topic) {
      cthulhuSubscribersByTopic_.insert(
          {topic,
           cthulhu::ptrWrap(context_.subscribeGeneric(
               desc.id(), subscriber.subscriber, nullptr, {cthulhu::ConsumerType::ASYNC}))});
      break;
    }
  }

  for (const auto& transformer : labgraphTransformers) {
    auto topicsBegin = transformer.publishedTopics.begin();
    auto topicsEnd = transformer.publishedTopics.end();
    if (std::find(topicsBegin, topicsEnd, topic) != topicsEnd &&
        cthulhuPublishersByTopic_.count(topic) == 0) {
      cthulhuPublishersByTopic_[topic] =
          cthulhu::ptrWrap(context_.advertise(desc.id(), desc.type()));
    }
    if (transformer.subscribedTopic == topic && cthulhuSubscribersByTopic_.count(topic) == 0) {
      cthulhuSubscribersByTopic_.insert(
          {topic,
           cthulhu::ptrWrap(context_.subscribeGeneric(
               desc.id(), transformer.transformer, nullptr, {cthulhu::ConsumerType::ASYNC}))});
    }
  }
}

std::vector<PublisherInfo> Node::getPublishers() {
  return {};
}

std::vector<SubscriberInfo> Node::getSubscribers() {
  return {};
}

std::vector<TransformerInfo> Node::getTransformers() {
  return {};
}

void Node::setup() {}
void Node::cleanup() {}

Node::~Node() {}

} // namespace labgraph
