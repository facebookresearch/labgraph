// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/StreamInterface.h>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

#include <cthulhu/Framework.h>

namespace cthulhu {

StreamSample::StreamSample() : metadata(std::make_shared<SampleMetadata>()) {}

StreamProducer::StreamProducer(StreamInterface* si, bool async) : async_(async) {
  if (si->hookProducer(this)) {
    producedStream_ = si;
  }
  if (async) {
    thread_ = std::thread(
        [this](std::future<void> signal) -> void {
          while (signal.wait_for(std::chrono::milliseconds(1)) == std::future_status::timeout) {
            std::queue<DataVariant> tempQueue;
            {
              std::lock_guard<std::mutex> lock(queueMutex_);
              std::swap(tempQueue, queue_);
            }
            while (!tempQueue.empty()) {
              DataVariant& item = tempQueue.front();
              if (item.type == DataVariant::Type::CONFIG) {
                producedStream_->configure(item.config);
              } else if (item.type == DataVariant::Type::SAMPLE) {
                producedStream_->sendSample(item.sample);
              }
              tempQueue.pop();
            }
          }
        },
        stopSignal_.get_future());
  }
}

StreamProducer::~StreamProducer() {
  if (producedStream_ != nullptr) {
    producedStream_->removeProducer(this);
  }
  if (async_) {
    stopSignal_.set_value();
    while (!thread_.joinable()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    thread_.join();
  }
};

// This should be called before producing any samples
void StreamProducer::configureStream(const StreamConfig& config) const {
  if (!async_) {
    producedStream_->configure(config);
  } else {
    DataVariant item;
    item.type = DataVariant::Type::CONFIG;
    item.config = std::move(config);
    std::lock_guard<std::mutex> lock(queueMutex_);
    queue_.push(std::move(item));
    if (queue_.size() > MAX_QUEUE_SIZE) {
      XR_LOGW_ONCE("sample dropped at configureStream, consider increasing MAX_QUEUE_SIZE");
      queue_.pop();
    }
  }
};

void StreamProducer::produceSample(const StreamSample& sample) const {
  if (!async_) {
    producedStream_->sendSample(sample);
  } else {
    DataVariant item;
    item.type = DataVariant::Type::SAMPLE;
    item.sample = std::move(sample);
    std::lock_guard<std::mutex> lock(queueMutex_);
    queue_.push(std::move(item));
    if (queue_.size() > MAX_QUEUE_SIZE) {
      XR_LOGW_ONCE("sample dropped at produceSample, consider increasing MAX_QUEUE_SIZE");
      queue_.pop();
    }
  }
};

const StreamConfig* StreamProducer::config() const {
  if (isActive() && producedStream_->isConfigured()) {
    return &producedStream_->config();
  }
  return nullptr;
};

StreamConsumer::StreamConsumer(
    StreamInterface* si,
    SampleCallback callback,
    ConfigCallback configCallback,
    bool async)
    : callback_(callback),
      configCallback_(configCallback),
      inhibitSampleCallback_(configCallback != nullptr),
      async_(async),
      performanceMonitor_{},
      queueCapacity_(DEFAULT_QUEUE_CAPACITY) {
  si->hookConsumer(this);
  consumedStream_ = si;

  if (async) {
    thread_ = std::thread(
        [this](std::future<void> signal) -> void {
          while (signal.wait_for(std::chrono::milliseconds(1)) == std::future_status::timeout) {
            try {
              Framework::validate();
            } catch (FrameworkCleanedUpException&) {
              break;
            }

            std::queue<DataVariant> tempQueue;
            {
              std::lock_guard<std::mutex> lock(queueMutex_);
              std::swap(tempQueue, queue_);
            }
            while (!tempQueue.empty()) {
              DataVariant& item = tempQueue.front();
              if (item.type == DataVariant::Type::CONFIG) {
                if (configCallback_ == nullptr) {
                  XR_LOGW("config received with no handler");
                } else {
                  inhibitSampleCallback_ = !configCallback_(item.config);
                }
              } else if (item.type == DataVariant::Type::SAMPLE) {
                if (!inhibitSampleCallback_) {
                  performanceMonitor_.startMeasurement();
                  callback_(item.sample);
                  performanceMonitor_.endMeasurement();
                }
              }
              tempQueue.pop();
            }
          }
        },
        stopSignal_.get_future());
  }
};

StreamConsumer::~StreamConsumer() {
  if (consumedStream_ != nullptr) {
    consumedStream_->removeConsumer(this);
  }

  if (async_) {
    stopSignal_.set_value();
    while (!thread_.joinable()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    thread_.join();
  }
};

void StreamConsumer::receiveConfig(const StreamConfig& config) const {
  if (configCallback_ != nullptr) {
    if (!async_) {
      inhibitSampleCallback_ = !configCallback_(config);
    } else {
      DataVariant item;
      item.type = DataVariant::Type::CONFIG;
      item.config = std::move(config);
      std::lock_guard<std::mutex> lock(queueMutex_);
      queue_.push(std::move(item));
      if (queue_.size() > queueCapacity_) {
        queue_.pop();
      }
    }
  }
};

void StreamConsumer::consumeSample(const StreamSample& sample) const {
  if (!async_) {
    if (!inhibitSampleCallback_) {
      performanceMonitor_.startMeasurement();
      callback_(sample);
      performanceMonitor_.endMeasurement();
    }
  } else {
    DataVariant item;
    item.type = DataVariant::Type::SAMPLE;
    item.sample = std::move(sample);
    std::lock_guard<std::mutex> lock(queueMutex_);
    queue_.push(std::move(item));
    if (queue_.size() > queueCapacity_) {
      queue_.pop();
      performanceMonitor_.sampleDropped();
    }
  }
}

PerformanceSummary StreamConsumer::getPerformanceSummary() const {
  return performanceMonitor_.getSummary();
}

uint64_t StreamConsumer::getQueueCapacity() const {
  std::lock_guard<std::mutex> lock(queueMutex_);
  return queueCapacity_;
}

void StreamConsumer::setQueueCapacity(uint64_t capacity) {
  std::lock_guard<std::mutex> lock(queueMutex_);
  queueCapacity_ = capacity;
}

} // namespace cthulhu
