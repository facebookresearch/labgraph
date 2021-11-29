#include <cthulhu/Dispatcher.h>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

Dispatcher::Dispatcher(Dispatcher&& other) {
  for (auto& producer : other.producers_) {
    producers_.push_back(IdentifiedProducer(producer.first, std::move(producer.second)));
  }
}

Dispatcher& Dispatcher::operator=(Dispatcher&& other) {
  for (auto& producer : other.producers_) {
    producers_.push_back(IdentifiedProducer(producer.first, std::move(producer.second)));
  }
  return *this;
}

void Dispatcher::registerProducer(StreamInterface* si) {
  producers_.push_back(
      IdentifiedProducer(si->description().id(), std::make_unique<StreamProducer>(si)));
};

void Dispatcher::dispatchSamples(const std::vector<StreamSample>& samples) {
  if (samples.size() != producers_.size()) {
    throw std::exception();
  }
  for (size_t i = 0; i < producers_.size(); i++) {
    if (!producers_[i].second->isActive()) {
      continue;
    }
    producers_[i].second->produceSample(samples[i]);
  }
};

void Dispatcher::dispatchConfigs(std::vector<StreamConfig>& configs) {
  if (configs.size() != producers_.size()) {
    throw std::exception();
  }
  for (size_t i = 0; i < producers_.size(); i++) {
    if (!producers_[i].second->isActive()) {
      continue;
    }
    producers_[i].second->configureStream(configs[i]);
  }
};

void Dispatcher::configureStream(const StreamConfig& config, uint32_t streamNumber) {
  if (streamNumber >= producers_.size()) {
    XR_LOGW("Dispatcher - Attempted to configure a stream with invalid streamNumber. Ignoring.");
    return;
  }
  producers_[streamNumber].second->configureStream(std::move(config));
};

const StreamConfig* Dispatcher::streamConfig(uint32_t streamNumber) {
  if (streamNumber >= producers_.size()) {
    XR_LOGW("Dispatcher - Attempted to configure a stream with invalid streamNumber. Ignoring.");
    return nullptr;
  }
  return producers_[streamNumber].second->config();
};

} // namespace cthulhu
