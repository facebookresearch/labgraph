#include <cthulhu/StreamType.h>

#include <cthulhu/Framework.h>

namespace cthulhu {

StreamConfig& ConfigAccessor::config(AutoStreamConfig* wrapper) {
  return wrapper->config_;
}

StreamSample& SampleAccessor::sample(AutoStreamSample* wrapper) {
  return wrapper->sample_;
}

AutoStreamConfig::AutoStreamConfig(size_t staticFieldSize, size_t dynamicFieldSize)
    : config_(staticFieldSize, dynamicFieldSize) {}

AutoStreamConfig::AutoStreamConfig(const StreamConfig& config) : config_(config) {}

AutoStreamConfig::~AutoStreamConfig() {}

const StreamConfig& AutoStreamConfig::getConfig() const {
  return config_;
}

void AutoStreamConfig::setConfig(const StreamConfig& config) {
  config_ = config;
}

SampleRate::SampleRate(AutoStreamConfig* wrapper) {
  wrapper_ = wrapper;
}

const double& SampleRate::get() const {
  return wrapper_->getConfig().nominalSampleRate;
}

SampleRate::operator const double&() const {
  return wrapper_->getConfig().nominalSampleRate;
}

void SampleRate::set(const double& value) {
  config(wrapper_).nominalSampleRate = value;
}

SampleRate& SampleRate::operator=(const double& value) {
  config(wrapper_).nominalSampleRate = value;
  return *this;
}

SampleSize::SampleSize(AutoStreamConfig* wrapper) {
  wrapper_ = wrapper;
}

uint32_t SampleSize::get() const {
  return wrapper_->getConfig().sampleSizeInBytes;
}

SampleSize::operator const uint32_t&() const {
  return wrapper_->getConfig().sampleSizeInBytes;
}

void SampleSize::set(const uint32_t& value) {
  config(wrapper_).sampleSizeInBytes = value;
}

SampleSize& SampleSize::operator=(const uint32_t& value) {
  config(wrapper_).sampleSizeInBytes = value;
  return *this;
}

AutoStreamSample::AutoStreamSample(size_t size, size_t numberDynamicFields) {
  if (size > 0) {
    sample_.parameters = Framework::instance().memoryPool()->getBufferFromPool("", size);
    memset(sample_.parameters.get(), 0, size);
  }
  if (numberDynamicFields > 0) {
    sample_.dynamicParameters = makeSharedRawDynamicArray(numberDynamicFields);
  }
}

AutoStreamSample::AutoStreamSample(
    const StreamSample& sample,
    size_t size,
    size_t numberDynamicFields)
    : sample_(sample) {
  if (!sample_.parameters && size > 0) {
    sample_.parameters = Framework::instance().memoryPool()->getBufferFromPool("", size);
    memset(sample_.parameters.get(), 0, size);
  }
  if (!sample_.dynamicParameters && numberDynamicFields > 0) {
    sample_.dynamicParameters = makeSharedRawDynamicArray(numberDynamicFields);
  }
}

AutoStreamSample ::~AutoStreamSample() {}

const StreamSample& AutoStreamSample::getSample() const {
  return sample_;
}

void AutoStreamSample::setSample(const StreamSample& sample) {
  sample_ = sample;
}

HeaderTimestamp::HeaderTimestamp(AutoStreamSample* wrapper) {
  wrapper_ = wrapper;
}

const double& HeaderTimestamp::get() const {
  return wrapper_->getSample().metadata->header.timestamp;
}

HeaderTimestamp::operator const double&() const {
  return wrapper_->getSample().metadata->header.timestamp;
}

void HeaderTimestamp::set(const double& value) {
  sample(wrapper_).metadata->header.timestamp = value;
}

HeaderTimestamp& HeaderTimestamp::operator=(const double& value) {
  sample(wrapper_).metadata->header.timestamp = value;
  return *this;
}

HeaderSequence::HeaderSequence(AutoStreamSample* wrapper) {
  wrapper_ = wrapper;
}

uint32_t HeaderSequence::get() const {
  return wrapper_->getSample().metadata->header.sequenceNumber;
}

HeaderSequence::operator const uint32_t&() const {
  return wrapper_->getSample().metadata->header.sequenceNumber;
}

void HeaderSequence::set(const uint32_t& value) {
  sample(wrapper_).metadata->header.sequenceNumber = value;
}

HeaderSequence& HeaderSequence::operator=(const uint32_t& value) {
  sample(wrapper_).metadata->header.sequenceNumber = value;
  return *this;
}

ProcessingTimestamp::ProcessingTimestamp(const std::string& stampName, AutoStreamSample* wrapper)
    : stampName_(stampName), wrapper_(wrapper) {
  // Add the named stamp to the sample if it doesn't exist
  wrapper_->getSample().metadata->processingStamps[stampName_];
}

const double& ProcessingTimestamp::get() const {
  return wrapper_->getSample().metadata->processingStamps.at(stampName_);
}

ProcessingTimestamp::operator const double&() const {
  return wrapper_->getSample().metadata->processingStamps.at(stampName_);
}

void ProcessingTimestamp::set(const double& value) {
  sample(wrapper_).metadata->processingStamps[stampName_] = value;
}

ProcessingTimestamp& ProcessingTimestamp::operator=(const double& value) {
  sample(wrapper_).metadata->processingStamps[stampName_] = value;
  return *this;
}

} // namespace cthulhu
