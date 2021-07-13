// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <cthulhu/Aligner.h>
#include <cthulhu/BufferTypes.h>
#include <cthulhu/Framework.h>
#include <cthulhu/PerformanceMonitor.h>
#include <cthulhu/bindings/cuda_util.h>
#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace cthulhu {

class PyContextRegistry {
 public:
  PyContextRegistry(cthulhu::ContextRegistryInterface* impl) : impl_(impl) {}

  auto contexts(bool all = false) const {
    return impl_->contexts(all);
  }

 private:
  const ContextRegistryInterface* impl_;
};

class PyTypeRegistry {
 public:
  PyTypeRegistry(cthulhu::TypeRegistryInterface* impl) : impl_(impl) {}
  ~PyTypeRegistry() = default;

  TypeInfoInterfacePtr findTypeName(const std::string& typeName) const {
    return impl_->findTypeName(typeName);
  }

  TypeInfoInterfacePtr findTypeID(uint32_t typeID) const {
    return impl_->findTypeID(typeID);
  }

  std::vector<std::string> typeNames() const {
    return impl_->typeNames();
  }

  void registerType(TypeDefinition definition) {
    // Python users can't specify C++ std:type_index, which means they can't
    // flip the switch to say that a stream type has or doesn't have a config.
    // We'll do that for them. If the definition has non-empty type fields, we
    // assume that there's a config type, and we'll flip the optional to a valid,
    // yet empty, type index.
    if (!definition.configFields.empty()) {
      definition.configType = typeid(nullptr);
    }
    impl_->registerType(std::move(definition));
  }

 private:
  TypeRegistryInterface* impl_;
};

class PyAnyBuffer;

class PyCpuBuffer {
 public:
  PyCpuBuffer() : PyCpuBuffer(nullptr, 0U) {}
  PyCpuBuffer(const CpuBuffer& data, size_t size) : data_(data), size_(size) {}
  PyCpuBuffer(CpuBuffer&& data, size_t size) : data_(std::move(data)), size_(size) {}
  PyCpuBuffer(const RawDynamic<>& rd) : data_(rd.raw), size_(rd.size()) {}
  ~PyCpuBuffer() = default;

  uint8_t* data() {
    return data_.get();
  }

  size_t size() const {
    return size_;
  }

  CpuBuffer dataRef() const {
    return data_;
  }

  RawDynamic<> toRawDynamic() const {
    RawDynamic<> rd;
    rd.raw = dataRef();
    rd.elementSize = sizeof(uint8_t);
    rd.elementCount = size();
    return rd;
  }

  inline PyAnyBuffer toAny() const;

 private:
  CpuBuffer data_;
  size_t size_;
};

class PyGpuBuffer {
 public:
  PyGpuBuffer() : PyGpuBuffer(GpuBuffer(), 0U) {}
  PyGpuBuffer(const GpuBuffer& data, size_t size) : data_(data), size_(size) {}
  PyGpuBuffer(GpuBuffer&& data, size_t size) : data_(std::move(data)), size_(size) {}
  ~PyGpuBuffer() = default;

  uint64_t handle() const {
    if (!data_) {
      return 0;
    }
    return data_.get()->handle;
  }

  PyCpuBuffer mapped() const {
    CpuBuffer mapped(data_.mapped());
    return PyCpuBuffer(mapped, mapped ? size_ : 0U);
  }

  size_t size() const {
    return size_;
  }

  uint32_t memoryTypeIndex() const {
    if (!data_) {
      return 0;
    }
    return data_.get()->memoryTypeIndex;
  }

  GpuBuffer dataRef() const {
    return data_;
  }

  /**
   * Note: This produces a handle that can be used with PyCUDA. However,
   * we have found that pycuda.driver.memcpy_htod fails when using this handle.
   * Therefore, it should only be used for device-to-device transfers. When
   * copying CPU data to this buffer from python, instead the user should
   * access it as a CpuBuffer.
   */
  uint64_t toCuda() const {
    return CudaUtil::instance().mapExternalMemoryHandle(data_->handle, size_);
  }

  inline PyAnyBuffer toAny() const;

 private:
  GpuBuffer data_;
  size_t size_;
};

class PyAnyBuffer {
 public:
  PyAnyBuffer() = default;
  PyAnyBuffer(const AnyBuffer& data, size_t size) : data_(data), size_(size) {}
  PyAnyBuffer(AnyBuffer&& data, size_t size) : data_(std::move(data)), size_(size) {}
  ~PyAnyBuffer() = default;

  PyAnyBuffer& operator=(const PyCpuBuffer& other) {
    data_ = other.dataRef();
    size_ = other.size();
    return *this;
  }

  size_t size() const {
    return size_;
  }

  PyCpuBuffer cpuBuffer() const {
    if (data_.type == BufferType::CPU) {
      return PyCpuBuffer(std::get<CpuBuffer>(data_.data), size_);
    } else if (data_.type == BufferType::GPU) {
      CpuBuffer mapped = std::get<GpuBuffer>(data_.data).mapped();
      return PyCpuBuffer(mapped, mapped ? size_ : 0U);
    }
    return PyCpuBuffer();
  }

  PyGpuBuffer gpuBuffer() const {
    if (data_.type == BufferType::GPU) {
      return PyGpuBuffer(std::get<GpuBuffer>(data_.data), size_);
    }
    return PyGpuBuffer();
  }

  AnyBuffer dataRef() const {
    return data_;
  }

 private:
  AnyBuffer data_;
  size_t size_;
};

PyAnyBuffer PyCpuBuffer::toAny() const {
  return PyAnyBuffer(data_, size_);
}

PyAnyBuffer PyGpuBuffer::toAny() const {
  return PyAnyBuffer(data_, size_);
}

class PyMemoryPool {
 public:
  PyMemoryPool(MemoryPoolInterface* impl) : impl_(impl) {}
  ~PyMemoryPool() = default;

  PyCpuBuffer getBufferFromPool(const std::string& id, size_t nrBytes) {
    return PyCpuBuffer(impl_->getBufferFromPool(id, nrBytes), nrBytes);
  }

  PyGpuBuffer getGpuBufferFromPool(size_t nrBytes, bool deviceLocal) {
    return PyGpuBuffer(impl_->getGpuBufferFromPool(nrBytes, deviceLocal), nrBytes);
  }

 private:
  MemoryPoolInterface* impl_;
};

class PyStreamConsumer;
class PyStreamProducer;
class PyAligner;

class PyStreamInterface {
 public:
  PyStreamInterface(StreamInterface* impl) : impl_(impl) {}
  ~PyStreamInterface() = default;

  const StreamDescription& description() const {
    return impl_->description();
  }

 private:
  StreamInterface* impl_;

  friend class PyStreamConsumer;
  friend class PyStreamProducer;
  friend class PyAligner;
};

class PyStreamConfig {
 public:
  PyStreamConfig() {}
  PyStreamConfig(PyCpuBuffer buffer) : size_(buffer.size()) {
    config_.parameters = buffer.dataRef();
  }
  PyStreamConfig(const StreamConfig& config, size_t size) : config_(config), size_(size) {}

  PyStreamConfig(const PyStreamConfig&) = default;
  PyStreamConfig& operator=(const PyStreamConfig&) = default;

  const double& getNominalSampleRate() {
    return config_.nominalSampleRate;
  }
  void setNominalSampleRate(const double& value) {
    config_.nominalSampleRate = value;
  }

  const uint32_t& getSampleSizeInBytes() {
    return config_.sampleSizeInBytes;
  }
  void setSampleSizeInBytes(const uint32_t& value) {
    config_.sampleSizeInBytes = value;
  }

  PyCpuBuffer getParameters() {
    return PyCpuBuffer(config_.parameters, size_);
  }
  void setParameters(const PyCpuBuffer& value) {
    size_ = value.size();
    config_.parameters = value.dataRef();
  }

  const StreamConfig& getConfig() const {
    return config_;
  }

 private:
  StreamConfig config_;
  size_t size_ = 0;

  friend class PyStreamProducer;
};

class PySampleMetadata;

using PySampleHistory = std::map<std::string, PySampleMetadata>;

class PyStreamSample;

class PySampleMetadata {
 public:
  PySampleMetadata(const std::shared_ptr<SampleMetadata>& data) : data_(data) {}
  ~PySampleMetadata() = default;

  const SampleHeader& getHeader() {
    return data_->header;
  }
  void setHeader(const SampleHeader& value) {
    data_->header = value;
  }

  const ProcessingStamps& getProcessingStamps() {
    return data_->processingStamps;
  }
  void setProcessingStamps(const ProcessingStamps& value) {
    data_->processingStamps = value;
  }

  const PySampleHistory getHistory() {
    PySampleHistory result;
    for (const auto& item : data_->history) {
      auto st = std::string(item.first);
      result.emplace(st, PySampleMetadata(item.second));
    }
    return result;
  }
  void setHistory(const PySampleHistory& value) {
    data_->history.clear();
    for (const auto& item : value) {
      data_->history[item.first] = item.second.data_;
    }
  }

 private:
  std::shared_ptr<SampleMetadata> data_;

  friend class PyStreamSample;
};

class PyDynamicParameters {
 public:
  PyDynamicParameters(const StreamSample& sample) : sample_(sample) {}

  PyCpuBuffer getDynamicParameter(const size_t index) const {
    RawDynamic<> rd = *(sample_.dynamicParameters.get() + index);
    return PyCpuBuffer(rd);
  }

  void setDynamicParameter(const size_t index, const PyCpuBuffer& buffer) {
    auto rdPtr = sample_.dynamicParameters.get() + index;
    *rdPtr = buffer.toRawDynamic();
  }

 private:
  StreamSample sample_;
};

class PyStreamSample {
 public:
  PyStreamSample() {}
  PyStreamSample(const StreamSample& sample, size_t payloadSize, size_t parameterSize)
      : sample_(sample), payloadSize_(payloadSize), parameterSize_(parameterSize) {}
  ~PyStreamSample() = default;

  PySampleMetadata getMetadata() {
    return PySampleMetadata(sample_.metadata);
  }
  void setMetadata(const PySampleMetadata& value) {
    sample_.metadata = value.data_;
  }

  std::optional<PyAnyBuffer> getPayload() {
    if (payloadSize_ == 0 || !sample_.payload) {
      return std::nullopt;
    }
    return PyAnyBuffer(sample_.payload, payloadSize_);
  }
  void setPayload(const PyAnyBuffer& value) {
    payloadSize_ = value.size();
    sample_.payload = value.dataRef();
  }

  const uint32_t& getNumberOfSubSamples() {
    return sample_.numberOfSubSamples;
  }
  void setNumberOfSubSamples(const uint32_t& value) {
    sample_.numberOfSubSamples = value;
  }

  std::optional<PyCpuBuffer> getParameters() {
    if (!sample_.parameters) {
      return std::nullopt;
    }
    return PyCpuBuffer(sample_.parameters, parameterSize_);
  }
  void setParameters(const PyCpuBuffer& value) {
    parameterSize_ = value.size();
    sample_.parameters = value.dataRef();
  }

  std::optional<PyDynamicParameters> getDynamicParameters() {
    if (!sample_.dynamicParameters) {
      return std::nullopt;
    }
    return PyDynamicParameters(sample_);
  }

  void setDynamicParameters(std::vector<PyCpuBuffer>& buffers) {
    sample_.dynamicParameters = makeSharedRawDynamicArray(buffers.size());
    PyDynamicParameters dp(sample_);
    for (size_t i = 0; i < buffers.size(); i++) {
      PyCpuBuffer buffer = buffers[i];
      dp.setDynamicParameter(i, buffer);
    }
  }

 private:
  StreamSample sample_;
  size_t payloadSize_ = 0;
  size_t parameterSize_ = 0;

  friend class PyStreamProducer;
};

using PySampleCallback = std::function<void(const PyStreamSample&)>;
using PyConfigCallback = std::function<bool(const PyStreamConfig&)>;

class PyStreamConsumer {
 public:
  PyStreamConsumer(
      const PyStreamInterface& si,
      const PySampleCallback& sampleCb,
      const PyConfigCallback& configCb,
      bool async) {
    pybind11::gil_scoped_release unlock;

    auto typeInfo =
        Framework::instance().typeRegistry()->findTypeID(si.impl_->description().type());
    auto typeName = typeInfo->typeName();

    const auto sampleParameterSize = typeInfo->sampleParameterSize();

    // SFoCB samples require a configuration to propagate the sample size,
    // even  if they're basic streams. Cache the sample size here.
    //
    // TODO there might be a better way to do this. However, the branch
    // below is general for all SFoCB types.
    if (typeInfo->hasSamplesInContentBlock()) {
      sampleSizeInBytes_.store(sampleParameterSize);
    }

    consumer_ = std::make_unique<StreamConsumer>(
        si.impl_,
        [this, sampleCb, sampleParameterSize](const StreamSample& sample) -> void {
          PyStreamSample pysample(
              sample, sample.numberOfSubSamples * sampleSizeInBytes_.load(), sampleParameterSize);
          pybind11::gil_scoped_acquire lock;
          sampleCb(pysample);
        },
        configCb ? std::function<bool(const StreamConfig&)>(
                       [this,
                        configCb,
                        configParameterSize =
                            Framework::instance()
                                .typeRegistry()
                                ->findTypeID(si.impl_->description().type())
                                ->configParameterSize()](const StreamConfig& config) -> bool {
                         sampleSizeInBytes_.store(config.sampleSizeInBytes);
                         PyStreamConfig pyconfig(config, configParameterSize);
                         pybind11::gil_scoped_acquire lock;
                         return configCb(pyconfig);
                       })
                 : nullptr,
        async);
  }

  void close() {
    pybind11::gil_scoped_release release;
    consumer_.reset();
  }

  bool isClosed() const {
    return nullptr == consumer_;
  }

  PerformanceSummary getPerformanceSummary() const {
    return consumer_->getPerformanceSummary();
  }

  uint64_t getQueueCapacity() const {
    return consumer_->getQueueCapacity();
  }

  void setQueueCapacity(uint64_t capacity) {
    consumer_->setQueueCapacity(capacity);
  }

  ~PyStreamConsumer() {
    close();
  }

 private:
  std::atomic<uint32_t> sampleSizeInBytes_;
  std::unique_ptr<StreamConsumer> consumer_;
};

class PyStreamProducer {
 public:
  PyStreamProducer(const PyStreamInterface& si, bool async)
      : producer_(std::in_place, si.impl_, async), si_(si.impl_) {}

  void produceSample(const PyStreamSample& sample) const {
    if (isClosed())
      throw std::runtime_error("StreamProducer is closed");

    StreamSample sampleOut = sample.sample_;
    // Determine the number of subsamples from the payload size
    sampleOut.numberOfSubSamples = sample.payloadSize_ / si_->config().sampleSizeInBytes;

    producer_->produceSample(sampleOut);
  }

  void configureStream(const PyStreamConfig& config) {
    if (isClosed())
      throw std::runtime_error("StreamProducer is closed");

    config_ = config;
    producer_->configureStream(config.config_);
  }

  void close() {
    pybind11::gil_scoped_release release;
    producer_.reset();
  }

  bool isClosed() const {
    return !producer_.has_value();
  }

  ~PyStreamProducer() {
    close();
  }

  const PyStreamConfig& getConfig() const {
    return config_;
  }

 private:
  std::optional<StreamProducer> producer_;
  StreamInterface* si_ = nullptr;
  PyStreamConfig config_;
};

class PyStreamRegistry {
 public:
  PyStreamRegistry(StreamRegistryInterface* impl) : impl_(impl) {}
  ~PyStreamRegistry() = default;

  PyStreamInterface registerStream(const StreamDescription& desc) {
    return PyStreamInterface(impl_->registerStream(desc));
  }

  std::optional<PyStreamInterface> getStream(const std::string& id) {
    StreamInterface* si = impl_->getStream(id);
    return si ? std::make_optional<PyStreamInterface>(si) : std::nullopt;
  }

  void printStreamInfo() {
    impl_->printStreamInfo();
  }

  std::vector<std::string> streamsOfTypeID(uint32_t typeID) {
    return impl_->streamsOfTypeID(typeID);
  }

 private:
  StreamRegistryInterface* impl_;
};

class PyClockManager {
 public:
  PyClockManager(ClockManagerInterface* impl) : impl_(impl) {}
  ~PyClockManager() = default;

  const std::shared_ptr<ControllableClockInterface> controlClock(const std::string& contextName) {
    return impl_->controlClock(contextName);
  }

  const std::shared_ptr<ClockInterface> clock() {
    return impl_->clock();
  }

 private:
  ClockManagerInterface* impl_;
};

class PyAligner : public Aligner {
 public:
  PyAligner(
      size_t queueSize = 1,
      ThreadPolicy threadPolicy = ThreadPolicy::THREAD_NEUTRAL,
      AlignerMode mode = AlignerMode::TIMESTAMP)
      : Aligner(queueSize, threadPolicy, mode){};
  virtual ~PyAligner() = default;

  void pyRegisterConsumer(const PyStreamInterface& si, int index) {
    registerConsumer(si.impl_, index);
  }

  void setAlignCallback(const std::function<bool(
                            const std::map<std::string, std::queue<StreamSample>>& queues,
                            std::vector<StreamSample>& samples)>& alignCallback) {
    alignCallback_ = alignCallback;
  }

  virtual void align() override {
    // Just execute the standard behavior if we haven't been given a callback
    if (!alignCallback_) {
      Aligner::align();
    }

    if (!finalized_) {
      return;
    }
    std::vector<StreamSample> samples;
    samples.reserve(queues_.size());
    {
      std::lock_guard<std::mutex> lock(queueMutex_);

      std::map<std::string, std::queue<StreamSample>> queues;
      for (const auto& queue : queues_) {
        queues[queue.id] = queue.samples;
      }

      if (!alignCallback_(queues, samples)) {
        return;
      }

      // Check to see if this set of samples should have a new config
      checkConfig(samples);
    }

    execute(samples);
  }

 private:
  std::function<bool(
      const std::map<std::string, std::queue<StreamSample>>& queues,
      std::vector<StreamSample>& samples)>
      alignCallback_;
};

class PyImageBuffer {
 public:
  PyImageBuffer() : PyImageBuffer(nullptr, 0U, 0U, 0U, 0U) {}
  PyImageBuffer(
      std::shared_ptr<uint8_t> data,
      size_t width,
      size_t height,
      size_t stride,
      size_t offset)
      : buffer_(std::move(data)),
        width_(width),
        height_(height),
        stride_(stride),
        offset_(offset) {}

  PyImageBuffer(PyImageBuffer&&) = default;
  PyImageBuffer& operator=(PyImageBuffer&&) = default;

  PyImageBuffer(const PyImageBuffer&) = delete;
  PyImageBuffer& operator=(const PyImageBuffer&) = delete;

  ~PyImageBuffer() = default;

  uint8_t* data() {
    return (buffer_) ? (buffer_.get() + offset_) : nullptr;
  }

  size_t width() const {
    return width_;
  }

  size_t height() const {
    return height_;
  }

  size_t stride() const {
    return stride_;
  }

  explicit operator bool() const {
    return (nullptr != buffer_);
  }

 private:
  std::shared_ptr<uint8_t> buffer_;
  size_t width_;
  size_t height_;
  size_t stride_;
  size_t offset_;
};

// Bindings entrypoint
namespace core {
void bindings(pybind11::module&);
}

} // namespace cthulhu
