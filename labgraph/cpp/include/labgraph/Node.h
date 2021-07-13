// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/Context.h>
#include <cthulhu/StreamInterface.h>

namespace labgraph {

/**
 * struct NodeTopic
 *
 * Describes a mapping between a LabGraph topic and a Cthulhu stream.
 */
struct NodeTopic {
  std::string topicName;
  cthulhu::StreamID streamID;
};

/**
 * struct NodeBootstrapInfo
 *
 * Contains all information needed to bootstrap a LabGraph C++ node into a state ready
 * for execution in an existing LabGraph graph.
 */
struct NodeBootstrapInfo {
  std::vector<NodeTopic> topics; // Mapping of LabGraph topics to Cthulhu streams
};

typedef std::function<void()> Publisher;
typedef std::function<void(const cthulhu::StreamSample&)> Subscriber;

/**
 * struct PublisherInfo
 *
 * Describes a publisher (its published topics and its main function).
 */
struct PublisherInfo {
  std::vector<std::string> publishedTopics;
  Publisher publisher;
};

/**
 * struct SubscriberInfo
 *
 * Describes a subscriber (its subscribed topic and its callback function).
 */
struct SubscriberInfo {
  SubscriberInfo(const std::string topic, Subscriber sub)
      : subscribedTopic(topic), subscriber(sub) {}
  std::string subscribedTopic;
  Subscriber subscriber;
};

/**
 * struct TransformerInfo
 *
 * Describes a transformer (its published topics, subscribed topic and its callback
 * function).
 */
struct TransformerInfo {
  std::vector<std::string> publishedTopics;
  std::string subscribedTopic;
  Subscriber transformer;
};

/**
 * class Node
 *
 * Describes a C++ node in a LabGraph graph.
 */
class Node {
 public:
  Node();
  virtual ~Node();

  /*** Setup function that is run when the LabGraph graph is starting up. */
  virtual void setup();

  /**
   * Entry point that is run in the LabGraph graph to start all the node's publishers.
   */
  void run();

  /*** Cleanup function that is run when the LabGraph graph is shutting down. */
  virtual void cleanup();

  /**
   * Bootstrapping function that is run by the LabGraph graph to connect this node's
   * topics with their corresponding Cthulhu streams.
   */
  void bootstrap(NodeBootstrapInfo& bootstrapInfo);

  virtual std::vector<std::string> getTopics() const = 0;
  virtual std::vector<PublisherInfo> getPublishers();
  virtual std::vector<SubscriberInfo> getSubscribers();
  virtual std::vector<TransformerInfo> getTransformers();

 protected:
  /**
   * Publishes a Cthulhu sample to a topic.
   *
   * @param topic The labgraph topic to publish to
   * @param sample The Cthulhu sample to publish
   */
  template <typename T>
  void publish(const std::string& topic, const T& sample);

 protected:
  cthulhu::Context context_;

  std::map<std::string, cthulhu::PublisherPtr> cthulhuPublishersByTopic_;
  std::multimap<std::string, cthulhu::SubscriberPtr> cthulhuSubscribersByTopic_;

  std::map<std::string, cthulhu::StreamID> streamIDsByTopic_;

 private:
  void bootstrapStream(const std::string& topic, const std::string& streamID);
};

}; // namespace labgraph

#include <labgraph/NodeImpl.h>
