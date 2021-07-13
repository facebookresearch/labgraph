// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/Aligner.h>

namespace cthulhu {

class QueueingAligner : public AlignerBase {
 public:
  QueueingAligner(const float& outputRate);
  virtual ~QueueingAligner();
  virtual void registerConsumer(StreamInterface* si, int index) override;

 protected:
  virtual void align() override;
  virtual void sampleCallback(size_t idx, const StreamSample& sample) override;
  virtual bool configCallback(size_t idx, const StreamConfig& config) override;

 private:
  float outputRate_;

  struct StreamQueue {
    std::deque<StreamSample> samples;
    StreamConfig config;
    bool hasConfig = false;
    uint32_t latestSequence = 0;
    std::unique_ptr<StreamConsumer> consumer;
    StreamID id;
  };
  std::vector<StreamQueue> queues_;
  std::mutex queueMutex_;

  bool configured_ = false;
}; // class QueueingAligner

} // namespace cthulhu
