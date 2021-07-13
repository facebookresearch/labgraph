// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/Aligner.h>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

AlignerBase::AlignerBase(ThreadPolicy threadPolicy) : policy_(threadPolicy), finalized_(false) {}

void AlignerBase::initThread() {
  if (policy_ == ThreadPolicy::SINGLE_THREADED && !thread_is_alive_) {
    thread_ = std::thread(
        [this](std::future<void> signal) -> void {
          while (signal.wait_for(std::chrono::milliseconds(1)) == std::future_status::timeout) {
            this->align();
          }
        },
        stopSignal_.get_future());
    thread_is_alive_ = true;
  }
}

void AlignerBase::killThread() {
  if (policy_ == ThreadPolicy::SINGLE_THREADED && thread_is_alive_) {
    stopSignal_.set_value();
    while (!thread_.joinable()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    thread_.join();
    thread_is_alive_ = false;
  }
}

AlignerBase::~AlignerBase() {
  killThread();
}

void AlignerBase::setCallback(const AlignerSampleCallback& callback) {
  callback_ = callback;
}

void AlignerBase::setConfigCallback(const AlignerConfigCallback& ccallback) {
  ccallback_ = ccallback;
}

void AlignerBase::setSamplesMetaCallback(const AlignerSamplesMetaCallback& smcallback) {
  smcallback_ = smcallback;
}

void AlignerBase::setConfigsMetaCallback(const AlignerConfigsMetaCallback& cmcallback) {
  cmcallback_ = cmcallback;
}

void AlignerBase::alignedCallback(const std::vector<StreamSample>& samples) {
  if (callback_) {
    callback_(samples);
  }
}

bool AlignerBase::alignedConfigCallback(const std::vector<StreamConfig>& configs) {
  if (ccallback_) {
    return ccallback_(configs);
  }
  return true;
}

void AlignerBase::alignedSamplesMetaCallback(const AlignerSamplesMeta& meta) {
  if (smcallback_) {
    return smcallback_(meta);
  }
}

void AlignerBase::alignedConfigsMetaCallback(const AlignerConfigsMeta& meta) {
  if (cmcallback_) {
    return cmcallback_(meta);
  }
}

void AlignerBase::finalize() {
  finalized_ = true;
}

bool AlignerBase::hasSampleCallback() const {
  return (nullptr != callback_);
}

Aligner::Aligner(
    size_t queueSize,
    ThreadPolicy threadPolicy,
    AlignerMode mode,
    double thresholdSeconds)
    : AlignerBase(threadPolicy), queueSize_(queueSize), threshold_(thresholdSeconds) {
  if (mode == AlignerMode::TIMESTAMP) {
    comparison_ = [this](const StreamSample& sample1, const StreamSample& sample2) -> bool {
      return std::fabs(sample1.metadata->header.timestamp - sample2.metadata->header.timestamp) <
          this->threshold_;
    };
  } else if (mode == AlignerMode::SEQUENCE) {
    comparison_ = [](const StreamSample& sample1, const StreamSample& sample2) -> bool {
      return sample1.metadata->header.sequenceNumber == sample2.metadata->header.sequenceNumber;
    };
  }
  initThread();
}

Aligner::~Aligner() {
  queues_.clear();
  killThread();
}

void Aligner::registerConsumer(StreamInterface* si, int index) {
  if (finalized_) {
    XR_LOGE("Attempted to register a consumer after being finalized.");
    return;
  }
  // We have to lock the queue mutex if we want to modify the queues_ structure,
  // since we could possibly be receiving data on another stream which needs
  // to be accessing its queue. Since calls to registerConsumer() are called from
  // a single thread, access to the properties of the queue for this particular index
  // are safe since the thread that will access this specific queue is not started until
  // construction of StreamConsumer.
  {
    std::lock_guard<std::mutex> lock(queueMutex_);
    if (queues_.size() <= index) {
      queues_.resize(index + 1);
    }
  }
  SampleCallback callback = [this, index](const StreamSample& sample) -> void {
    sampleCallback(index, sample);
  };
  ConfigCallback ccallback = [this, index](const StreamConfig& config) -> bool {
    return configCallback(index, config);
  };
  queues_[index].id = si->description().id();
  queues_[index].consumer = std::make_unique<StreamConsumer>(si, callback, ccallback);
}

void Aligner::checkConfig(const std::vector<StreamSample>& samples) {
  // Check to see if this set of samples should have a new config
  bool updateConfig = !configured_;
  size_t idx = 0;
  for (auto& queue : queues_) {
    while (queue.configs.size() > 1 &&
           queue.configs[1].first < samples[idx].metadata->header.sequenceNumber) {
      updateConfig = true;
      queue.configs.pop_front();
    }
    ++idx;
  }
  if (updateConfig) {
    std::vector<StreamConfig> configs;
    configs.reserve(queues_.size());
    AlignerConfigsMeta meta;
    meta.reserve(queues_.size());
    for (const auto& queue : queues_) {
      if (queue.configs.empty()) {
        break;
      }
      configs.push_back(queue.configs.front().second);
      meta.push_back(AlignerStreamMeta{queue.id, queue.configs.front().second.sampleSizeInBytes});
    }
    if (configs.size() == queues_.size()) {
      inhibitSampleCallback_ = !alignedConfigCallback(configs);
      configured_ = true;
      alignedConfigsMetaCallback(meta);
    }
  }
}

void Aligner::execute(const std::vector<StreamSample>& samples) {
  if (!inhibitSampleCallback_) {
    // Produce aligned metadata
    AlignerSamplesMeta meta(samples.size());
    for (size_t i = 0; i < samples.size(); i++) {
      meta[i].timestamp = samples[i].metadata->header.timestamp;
      meta[i].references.resize(1);
      meta[i].references[0].sequenceNumber = samples[i].metadata->header.sequenceNumber;
      meta[i].references[0].subSampleOffset = 0;
      meta[i].references[0].numSubSamples = samples[i].numberOfSubSamples;
    }
    alignedSamplesMetaCallback(meta);

    alignedCallback(samples);
  }
}

void Aligner::sampleCallback(size_t idx, const StreamSample& sample) {
  {
    std::lock_guard<std::mutex> lock(queueMutex_);
    queues_[idx].latestSequence = sample.metadata->header.sequenceNumber;
    queues_[idx].samples.push(sample);

    if (queues_[idx].samples.size() > queueSize_) {
      queues_[idx].samples.pop();
    }
  }
  if (policy_ == ThreadPolicy::THREAD_NEUTRAL) {
    align();
  }
}

void Aligner::align() {
  if (!finalized_) {
    return;
  }
  std::vector<StreamSample> samples;
  samples.reserve(queues_.size());
  {
    std::lock_guard<std::mutex> lock(queueMutex_);
    const StreamSample* refSample = nullptr;

    for (auto& queue : queues_) {
      if (queue.samples.empty()) {
        return;
      }

      if (refSample == nullptr) {
        refSample = &queue.samples.front();
        continue;
      }

      if (!comparison_(*refSample, queue.samples.front())) {
        return;
      }
    }

    if (refSample == nullptr) {
      return;
    }

    for (auto& queue : queues_) {
      samples.push_back(queue.samples.front());
      queue.samples.pop();
    }

    // Check to see if this set of samples should have a new config
    checkConfig(samples);
  }

  execute(samples);
}

bool Aligner::configCallback(size_t idx, const StreamConfig& config) {
  std::lock_guard<std::mutex> lock(queueMutex_);
  queues_[idx].configs.push_back(
      std::pair<uint32_t, StreamConfig>(queues_[idx].latestSequence, config));
  return true;
}

} // namespace cthulhu
