// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cmath>
#include <future>
#include <queue>

#include <cthulhu/AlignerMeta.h>
#include <cthulhu/StreamInterface.h>

namespace cthulhu {

using AlignerSampleCallback = std::function<void(const std::vector<StreamSample>&)>;
using AlignerConfigCallback = std::function<bool(const std::vector<StreamConfig>&)>;
using AlignerSamplesMetaCallback = std::function<void(const AlignerSamplesMeta&)>;
using AlignerConfigsMetaCallback = std::function<void(const AlignerConfigsMeta&)>;

// Thread policies are:
//  - THREAD_NEUTRAL: Aligner/Dispatcher do not spawn any new threads. For example, the thread that
//                    calls sampleCallback will also call alignedCallback
//  - SINGLE_THREADED: Aligner/Dispatcher spawns a new thread. For example, the thread that calls
//                     sampleCallback will not call alignedCallback, this will be a new thread
enum class ThreadPolicy : uint8_t { THREAD_NEUTRAL = 0, SINGLE_THREADED = 1 };

class AlignerBase {
 public:
  AlignerBase(ThreadPolicy threadPolicy = ThreadPolicy::THREAD_NEUTRAL);
  virtual ~AlignerBase();

  // These registration function is not thread safe, and should be
  // followed by a call to finalize()
  virtual void registerConsumer(StreamInterface* si, int index) = 0;

  void setCallback(const AlignerSampleCallback& callback);
  void setConfigCallback(const AlignerConfigCallback& callback);
  void setSamplesMetaCallback(const AlignerSamplesMetaCallback& callback);
  void setConfigsMetaCallback(const AlignerConfigsMetaCallback& callback);

  // This should be called once all consumers are registered
  // align() should only be called once we are finalized, and
  // we cannot be un-finalized (the transition is uni-directional)
  void finalize();

  // Clear the aligner's internal sample state, if any.
  //
  // This is an optional method, and aligner users may not call clear().
  virtual void clear() { /* Default implementation does nothing */
  }

 protected:
  virtual void align() = 0;
  virtual void sampleCallback(size_t idx, const StreamSample& sample) = 0;
  virtual bool configCallback(size_t idx, const StreamConfig& config) = 0;

  void initThread();
  void killThread();

  void alignedCallback(const std::vector<StreamSample>& samples);
  bool alignedConfigCallback(const std::vector<StreamConfig>& configs);
  void alignedSamplesMetaCallback(const AlignerSamplesMeta& meta);
  void alignedConfigsMetaCallback(const AlignerConfigsMeta& meta);

  bool hasSampleCallback() const;

  AlignerSampleCallback callback_ = nullptr;
  AlignerConfigCallback ccallback_ = nullptr;
  AlignerSamplesMetaCallback smcallback_ = nullptr;
  AlignerConfigsMetaCallback cmcallback_ = nullptr;

  ThreadPolicy policy_;
  std::thread thread_;
  std::promise<void> stopSignal_;
  bool thread_is_alive_ = false;

  bool inhibitSampleCallback_ = false;

  std::atomic<bool> finalized_;
}; // class AlignerBase

enum class AlignerMode : uint32_t { TIMESTAMP = 0, SEQUENCE = 1 };

class Aligner : public AlignerBase {
 public:
  Aligner(
      size_t queueSize = 1,
      ThreadPolicy threadPolicy = ThreadPolicy::THREAD_NEUTRAL,
      AlignerMode mode = AlignerMode::TIMESTAMP,
      double thresholdSeconds = 0.005);

  virtual ~Aligner();

 protected:
  virtual void align() override;
  virtual void sampleCallback(size_t idx, const StreamSample& sample) override;
  virtual bool configCallback(size_t idx, const StreamConfig& config) override;

 public:
  virtual void registerConsumer(StreamInterface* si, int index) override;

 protected:
  void checkConfig(const std::vector<StreamSample>& samples);
  void execute(const std::vector<StreamSample>& samples);

  struct StreamQueue {
    std::queue<StreamSample> samples;
    std::deque<std::pair<uint32_t, StreamConfig>> configs;
    uint32_t latestSequence = 0;
    std::unique_ptr<StreamConsumer> consumer;
    StreamID id;
  };

  std::vector<StreamQueue> queues_;
  size_t queueSize_;
  // This enables multi-threaded access to the queues_ via sampleCallback. The public functions
  // are not thread-safe.
  std::mutex queueMutex_;
  double threshold_;
  std::function<bool(const StreamSample& sample1, const StreamSample& sample2)> comparison_;
  bool configured_ = false;
}; // class Aligner

} // namespace cthulhu
