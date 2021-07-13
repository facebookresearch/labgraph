// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/QueueingAligner.h>

#include <cthulhu/Framework.h>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

#include <numeric>

namespace cthulhu {

QueueingAligner::QueueingAligner(const float& outputRate)
    : AlignerBase(ThreadPolicy::SINGLE_THREADED), outputRate_(outputRate) {
  initThread();
}

QueueingAligner::~QueueingAligner() {}

// Note: This is copy-paste from the standard Aligner
void QueueingAligner::registerConsumer(StreamInterface* si, int index) {
  if (finalized_) {
    XR_LOGE("Attempted to register a consumer after being finalized.");
    return;
  }
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

void QueueingAligner::align() {
  if (!finalized_) {
    return;
  }

  std::chrono::time_point<std::chrono::steady_clock> start = std::chrono::steady_clock::now();

  std::vector<StreamSample> samples;
  samples.reserve(queues_.size());
  AlignerSamplesMeta samplesMeta;
  samplesMeta.reserve(queues_.size());
  {
    // We're safe to access queues_.size() outside of the lock,
    // since we guarantee that the size will not change after
    // finalization.
    std::lock_guard<std::mutex> lock(queueMutex_);

    if (!configured_) {
      // Try to configure
      bool updateConfig = true;
      for (auto& queue : queues_) {
        updateConfig = updateConfig && queue.hasConfig;
      }
      if (updateConfig) {
        std::vector<StreamConfig> configs;
        configs.reserve(queues_.size());
        AlignerConfigsMeta meta;
        meta.reserve(queues_.size());
        for (const auto& queue : queues_) {
          configs.push_back(queue.config);
          meta.push_back(AlignerStreamMeta{queue.id, queue.config.sampleSizeInBytes});
        }
        inhibitSampleCallback_ = !alignedConfigCallback(configs);
        configured_ = true;
        alignedConfigsMetaCallback(meta);
      }
    }

    if (configured_) {
      // Aggregate samples and meta
      for (auto& queue : queues_) {
        StreamSample sample;
        AlignerSampleMeta meta;
        if (!queue.samples.empty()) {
          sample.parameters = queue.samples.front().parameters;
          sample.metadata = queue.samples.front().metadata;
          meta.timestamp = queue.samples.front().metadata->header.timestamp;
          // TBD: Should we propagate the history timestamps all of inputs?
        }
        // Note: we still propagate empty samples
        int payloadSize = std::accumulate(
            queue.samples.begin(),
            queue.samples.end(),
            0,
            [](int val, const StreamSample& next) -> int { return val + next.numberOfSubSamples; });
        sample.payload = Framework::instance().memoryPool()->getBufferFromPool(
            queue.id, payloadSize * queue.config.sampleSizeInBytes);
        meta.references.reserve(queue.samples.size());
        int index = 0;
        for (const auto& inputSample : queue.samples) {
          AlignerReferenceMeta reference;
          std::memcpy(
              ((CpuBuffer)sample.payload).get() + index * queue.config.sampleSizeInBytes,
              ((CpuBuffer)inputSample.payload).get(),
              inputSample.numberOfSubSamples * queue.config.sampleSizeInBytes);
          index += inputSample.numberOfSubSamples;
          reference.sequenceNumber = inputSample.metadata->header.sequenceNumber;
          reference.subSampleOffset = 0;
          reference.numSubSamples = inputSample.numberOfSubSamples;
          meta.references.push_back(reference);
        }
        sample.numberOfSubSamples = payloadSize;
        samples.push_back(sample);
        samplesMeta.push_back(meta);
        queue.samples.clear();
      }
    }
  }

  if (samples.size() == queues_.size()) {
    if (!inhibitSampleCallback_) {
      alignedSamplesMetaCallback(samplesMeta);
      alignedCallback(samples);
    }
  }

  std::chrono::time_point<std::chrono::steady_clock> end = std::chrono::steady_clock::now();
  auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
  // The AlignerBase will sleep for 1ms, so offset this in our calculation
  int delayInMs = (1000.0 / outputRate_) - ms - 1.0;
  if (delayInMs > 0.0) {
    std::this_thread::sleep_for(std::chrono::milliseconds(delayInMs));
  }
}

void QueueingAligner::sampleCallback(size_t idx, const StreamSample& sample) {
  {
    std::lock_guard<std::mutex> lock(queueMutex_);
    queues_[idx].latestSequence = sample.metadata->header.sequenceNumber;
    queues_[idx].samples.push_back(sample);
  }
}

bool QueueingAligner::configCallback(size_t idx, const StreamConfig& config) {
  std::unique_lock<std::mutex> lock(queueMutex_);
  if (queues_[idx].hasConfig) {
    lock.unlock();
    XR_LOGE(
        "QueueingAligner received reconfiguration on a stream, which it does not support. "
        "Turning off...");
    return false;
  }
  queues_[idx].config = config;
  queues_[idx].hasConfig = true;
  return true;
}

} // namespace cthulhu
