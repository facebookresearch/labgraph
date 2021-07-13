// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/bindings/core.h>
#include <pybind11/chrono.h>
#include <pybind11/iostream.h>

#include <sstream>

namespace py = pybind11;

namespace cthulhu {

namespace core {

void bindings(py::module_& m) {
  m.doc() = "cthulhubindings: lower-level bindings to Cthulhu";

  py::class_<cthulhu::ContextInfoInterface, std::shared_ptr<cthulhu::ContextInfoInterface>>(
      m, "ContextInfo")
      .def_property_readonly("name", &cthulhu::ContextInfoInterface::name)
      .def_property_readonly("private_ns", &cthulhu::ContextInfoInterface::isPrivateNamespace)
      .def_property_readonly("pid", &cthulhu::ContextInfoInterface::getPid)
      .def_property_readonly("valid", &cthulhu::ContextInfoInterface::getValid)
      .def_property_readonly("subscriptions", &cthulhu::ContextInfoInterface::subscriptions)
      .def_property_readonly("publications", &cthulhu::ContextInfoInterface::publications)
      .def_property_readonly("transformations", &cthulhu::ContextInfoInterface::transformations)
      .def("__repr__", [](const cthulhu::ContextInfoInterface& ctx) {
        std::ostringstream output;
        output << "<ContextInfo -- name: " << ctx.name()
               << ", private ns: " << ctx.isPrivateNamespace() << ", pid: " << ctx.getPid()
               << ", valid: " << ctx.getValid() << " >";
        return output.str();
      });

  py::class_<cthulhu::PyContextRegistry>(m, "ContextRegistry")
      .def("contexts", &cthulhu::PyContextRegistry::contexts, py::arg("all") = false);

  m.def("contextRegistry", []() -> std::optional<cthulhu::PyContextRegistry> {
    if (cthulhu::Framework::instance().contextRegistry()) {
      return cthulhu::PyContextRegistry(cthulhu::Framework::instance().contextRegistry());
    }
    return {};
  });

  py::class_<cthulhu::Field>(m, "Field")
      .def(py::init<uint32_t, uint32_t, const std::string, uint32_t>())
      .def(py::init<uint32_t, uint32_t, const std::string, uint32_t, bool>())
      .def_readwrite("offset", &cthulhu::Field::offset)
      .def_readwrite("size", &cthulhu::Field::size)
      .def_readwrite("typeName", &cthulhu::Field::typeName)
      .def_readwrite("numElements", &cthulhu::Field::numElements)
      .def_readwrite("isDynamic", &cthulhu::Field::isDynamic)
      .def("__eq__", [](const cthulhu::Field& left, const cthulhu::Field& right) {
        return left == right;
      });

  py::class_<cthulhu::TypeDefinition>(m, "TypeDefinition")
      .def(py::init<>())
      .def_readwrite("typeName", &cthulhu::TypeDefinition::typeName)
      // Skip sampleType; can't be expressed in Python
      // Skip configType; can't be expressed in Python
      .def_readwrite("sampleParameterSize", &cthulhu::TypeDefinition::sampleParameterSize)
      .def_readwrite("configParameterSize", &cthulhu::TypeDefinition::configParameterSize)
      .def_readwrite(
          "sampleNumberDynamicFields", &cthulhu::TypeDefinition::sampleNumberDynamicFields)
      .def_readwrite(
          "configNumberDynamicFields", &cthulhu::TypeDefinition::configNumberDynamicFields)
      .def_readwrite("sampleFields", &cthulhu::TypeDefinition::sampleFields)
      .def_readwrite("configFields", &cthulhu::TypeDefinition::configFields)
      .def_readwrite("hasContentBlock", &cthulhu::TypeDefinition::hasContentBlock)
      .def_readwrite(
          "hasSamplesInContentBlock", &cthulhu::TypeDefinition::hasSamplesInContentBlock);

  py::class_<cthulhu::TypeInfoInterface, std::shared_ptr<cthulhu::TypeInfoInterface>>(m, "TypeInfo")
      .def_property_readonly("hasContentBlock", &cthulhu::TypeInfoInterface::hasContentBlock)
      .def_property_readonly(
          "hasSamplesInContentBlock", &cthulhu::TypeInfoInterface::hasSamplesInContentBlock)
      .def_property_readonly("typeName", &cthulhu::TypeInfoInterface::typeName)
      .def_property_readonly("typeID", &cthulhu::TypeInfoInterface::typeID)
      .def_property_readonly("isBasic", &cthulhu::TypeInfoInterface::isBasic)
      .def_property_readonly(
          "sampleParameterSize", &cthulhu::TypeInfoInterface::sampleParameterSize)
      .def_property_readonly(
          "configParameterSize", &cthulhu::TypeInfoInterface::configParameterSize)
      .def_property_readonly("sampleFields", &cthulhu::TypeInfoInterface::sampleFields)
      .def_property_readonly("configFields", &cthulhu::TypeInfoInterface::configFields);

  py::class_<cthulhu::PyTypeRegistry>(m, "TypeRegistry")
      .def("findTypeName", &cthulhu::PyTypeRegistry::findTypeName)
      .def("findTypeID", &cthulhu::PyTypeRegistry::findTypeID)
      .def("typeNames", &cthulhu::PyTypeRegistry::typeNames)
      .def("registerType", &cthulhu::PyTypeRegistry::registerType);

  m.def("typeRegistry", []() -> std::optional<cthulhu::PyTypeRegistry> {
    if (cthulhu::Framework::instance().typeRegistry()) {
      return cthulhu::PyTypeRegistry(cthulhu::Framework::instance().typeRegistry());
    }
    return {};
  });

  py::class_<cthulhu::PyCpuBuffer>(m, "CpuBuffer", py::buffer_protocol())
      .def_buffer([](cthulhu::PyCpuBuffer& b) -> py::buffer_info {
        return py::buffer_info(
            b.data(),
            sizeof(uint8_t),
            py::format_descriptor<uint8_t>::format(),
            1,
            {b.size()},
            {sizeof(uint8_t)});
      })
      .def("__len__", &cthulhu::PyCpuBuffer::size)
      .def_static(
          "new",
          [](size_t size) -> PyCpuBuffer {
            return cthulhu::PyCpuBuffer(
                std::shared_ptr<uint8_t>(new uint8_t[size]{0}, std::default_delete<uint8_t[]>()),
                size);
          })
      .def(py::init([](py::buffer b) {
        py::buffer_info info = b.request();
        // Create a non-owning pointer that just captures and holds a buffer reference
        return cthulhu::PyCpuBuffer(
            std::shared_ptr<uint8_t>((uint8_t*)info.ptr, [b](uint8_t* ptr) {}),
            (size_t)(info.shape[0] * info.itemsize));
      }))
      .def("toAny", &cthulhu::PyCpuBuffer::toAny);

  py::class_<cthulhu::PyGpuBuffer>(m, "GpuBuffer")
      .def("mapped", &cthulhu::PyGpuBuffer::mapped)
      .def("handle", &cthulhu::PyGpuBuffer::handle)
      .def("size", &cthulhu::PyGpuBuffer::size)
      .def("memoryTypeIndex", &cthulhu::PyGpuBuffer::memoryTypeIndex)
      .def("toCuda", &cthulhu::PyGpuBuffer::toCuda)
      .def("toAny", &cthulhu::PyGpuBuffer::toAny);

  py::class_<cthulhu::PyAnyBuffer>(m, "AnyBuffer")
      .def("cpuBuffer", &cthulhu::PyAnyBuffer::cpuBuffer)
      .def("gpuBuffer", &cthulhu::PyAnyBuffer::gpuBuffer);

  py::class_<cthulhu::PyMemoryPool>(m, "MemoryPool")
      .def("getBufferFromPool", &cthulhu::PyMemoryPool::getBufferFromPool)
      .def("getGpuBufferFromPool", &cthulhu::PyMemoryPool::getGpuBufferFromPool);

  m.def("memoryPool", []() -> std::optional<cthulhu::PyMemoryPool> {
    if (cthulhu::Framework::instance().memoryPool()) {
      return cthulhu::PyMemoryPool(cthulhu::Framework::instance().memoryPool());
    }
    return {};
  });

  py::class_<cthulhu::StreamDescription>(m, "StreamDescription")
      .def(py::init<std::string, uint32_t>())
      .def_property_readonly("id", &cthulhu::StreamDescription::id)
      .def_property_readonly("type", &cthulhu::StreamDescription::type);

  py::class_<cthulhu::PyStreamInterface>(m, "StreamInterface")
      .def_property_readonly("description", &cthulhu::PyStreamInterface::description);

  py::class_<cthulhu::PyStreamConfig>(m, "StreamConfig")
      .def(py::init<cthulhu::PyCpuBuffer>())
      .def_property(
          "nominalSampleRate",
          &cthulhu::PyStreamConfig::getNominalSampleRate,
          &cthulhu::PyStreamConfig::setNominalSampleRate)
      .def_property(
          "sampleSizeInBytes",
          &cthulhu::PyStreamConfig::getSampleSizeInBytes,
          &cthulhu::PyStreamConfig::setSampleSizeInBytes)
      .def_property(
          "parameters",
          &cthulhu::PyStreamConfig::getParameters,
          &cthulhu::PyStreamConfig::setParameters);

  py::class_<cthulhu::SampleHeader>(m, "SampleHeader")
      .def_readwrite("timestamp", &cthulhu::SampleHeader::timestamp)
      .def_readwrite("sequenceNumber", &cthulhu::SampleHeader::sequenceNumber);

  py::class_<cthulhu::PySampleMetadata>(m, "SampleMetadata")
      .def_property(
          "header", &cthulhu::PySampleMetadata::getHeader, &cthulhu::PySampleMetadata::setHeader)
      .def_property(
          "processingStamps",
          &cthulhu::PySampleMetadata::getProcessingStamps,
          &cthulhu::PySampleMetadata::setProcessingStamps)
      .def_property(
          "history",
          &cthulhu::PySampleMetadata::getHistory,
          &cthulhu::PySampleMetadata::setHistory);

  py::class_<cthulhu::PyDynamicParameters>(m, "DynamicParameters")
      .def("__getitem__", &cthulhu::PyDynamicParameters::getDynamicParameter)
      .def("__setitem__", &cthulhu::PyDynamicParameters::setDynamicParameter);

  py::class_<cthulhu::PyStreamSample>(m, "StreamSample")
      .def(py::init())
      .def_property(
          "metadata", &cthulhu::PyStreamSample::getMetadata, &cthulhu::PyStreamSample::setMetadata)
      .def_property(
          "numberOfSubSamples",
          &cthulhu::PyStreamSample::getNumberOfSubSamples,
          &cthulhu::PyStreamSample::setNumberOfSubSamples)
      .def_property(
          "payload", &cthulhu::PyStreamSample::getPayload, &cthulhu::PyStreamSample::setPayload)
      .def_property(
          "parameters",
          &cthulhu::PyStreamSample::getParameters,
          &cthulhu::PyStreamSample::setParameters)
      .def_property(
          "dynamicParameters",
          &cthulhu::PyStreamSample::getDynamicParameters,
          &cthulhu::PyStreamSample::setDynamicParameters);

  py::class_<cthulhu::PyStreamConsumer>(m, "StreamConsumer")
      .def(
          py::init<
              cthulhu::PyStreamInterface,
              cthulhu::PySampleCallback,
              cthulhu::PyConfigCallback,
              bool>(),
          py::arg("si"),
          py::arg("sampleCb"),
          py::arg("configCb") = nullptr,
          py::arg("async") = false)
      .def("close", &cthulhu::PyStreamConsumer::close)
      .def_property_readonly("closed", &cthulhu::PyStreamConsumer::isClosed)
      .def("get_performance_summary", &cthulhu::PyStreamConsumer::getPerformanceSummary)
      .def_property(
          "queue_capacity",
          &cthulhu::PyStreamConsumer::getQueueCapacity,
          &cthulhu::PyStreamConsumer::setQueueCapacity)
      .def("__bool__", [](const cthulhu::PyStreamConsumer& cons) -> bool {
        return !cons.isClosed();
      });

  py::class_<cthulhu::PyStreamProducer>(m, "StreamProducer")
      .def(py::init<cthulhu::PyStreamInterface, bool>(), py::arg("si"), py::arg("async") = false)
      .def("close", &cthulhu::PyStreamProducer::close)
      .def_property_readonly("closed", &cthulhu::PyStreamProducer::isClosed)
      .def_property_readonly("config", &cthulhu::PyStreamProducer::getConfig)
      .def("produceSample", &cthulhu::PyStreamProducer::produceSample)
      .def("configureStream", &cthulhu::PyStreamProducer::configureStream)
      .def("__bool__", [](const cthulhu::PyStreamProducer& prod) -> bool {
        return !prod.isClosed();
      });

  py::class_<cthulhu::PyStreamRegistry>(m, "StreamRegistry")
      .def("registerStream", &cthulhu::PyStreamRegistry::registerStream)
      .def("getStream", &cthulhu::PyStreamRegistry::getStream)
      .def("printStreamInfo", &cthulhu::PyStreamRegistry::printStreamInfo)
      .def("streamsOfTypeID", &cthulhu::PyStreamRegistry::streamsOfTypeID);

  m.def("streamRegistry", []() -> std::optional<cthulhu::PyStreamRegistry> {
    if (cthulhu::Framework::instance().streamRegistry()) {
      return cthulhu::PyStreamRegistry(cthulhu::Framework::instance().streamRegistry());
    }
    return {};
  });

  py::enum_<cthulhu::ClockEvent>(m, "ClockEvent")
      .value("START", cthulhu::ClockEvent::START)
      .value("PAUSE", cthulhu::ClockEvent::PAUSE)
      .value("RTF_UPDATE", cthulhu::ClockEvent::RTF_UPDATE)
      .value("JUMP", cthulhu::ClockEvent::JUMP)
      .export_values();

  py::class_<cthulhu::ClockInterface, std::shared_ptr<cthulhu::ClockInterface>>(m, "Clock")
      .def("getTime", &cthulhu::ClockInterface::getTime)
      .def("isSimulated", &cthulhu::ClockInterface::isSimulated)
      .def("listenEvents", &cthulhu::ClockInterface::listenEvents);

  py::class_<
      cthulhu::ControllableClockInterface,
      std::shared_ptr<cthulhu::ControllableClockInterface>>(m, "ControllableClock")
      .def("start", &cthulhu::ControllableClockInterface::start)
      .def("pause", &cthulhu::ControllableClockInterface::pause)
      .def("setRealtimeFactor", &cthulhu::ControllableClockInterface::setRealtimeFactor)
      .def("setTime", &cthulhu::ControllableClockInterface::setTime);

  py::class_<cthulhu::PyClockManager>(m, "ClockManager")
      .def("controlClock", &cthulhu::PyClockManager::controlClock)
      .def("clock", &cthulhu::PyClockManager::clock);

  py::class_<cthulhu::ClockAuthority>(m, "ClockAuthority")
      .def(py::init<bool, const std::string&>());

  m.def("clockManager", []() -> std::optional<cthulhu::PyClockManager> {
    if (cthulhu::Framework::instance().clockManager()) {
      return cthulhu::PyClockManager(cthulhu::Framework::instance().clockManager());
    }
    return {};
  });

  py::enum_<cthulhu::ThreadPolicy>(m, "ThreadPolicy")
      .value("THREAD_NEUTRAL", cthulhu::ThreadPolicy::THREAD_NEUTRAL)
      .value("SINGLE_THREADED", cthulhu::ThreadPolicy::SINGLE_THREADED)
      .export_values();

  py::enum_<cthulhu::AlignerMode>(m, "AlignerMode")
      .value("TIMESTAMP", cthulhu::AlignerMode::TIMESTAMP)
      .value("SEQUENCE", cthulhu::AlignerMode::SEQUENCE)
      .export_values();

  py::class_<cthulhu::PyAligner>(m, "Aligner")
      .def(py::init())
      .def(py::init<size_t, cthulhu::ThreadPolicy, cthulhu::AlignerMode>())
      .def("registerConsumer", &cthulhu::PyAligner::pyRegisterConsumer)
      .def("setCallback", &cthulhu::PyAligner::setCallback)
      .def("setConfigCallback", &cthulhu::PyAligner::setConfigCallback)
      .def("setSamplesMetaCallback", &cthulhu::PyAligner::setSamplesMetaCallback)
      .def("setConfigsMetaCallback", &cthulhu::PyAligner::setConfigsMetaCallback)
      .def("finalize", &cthulhu::PyAligner::finalize)
      .def("setAlignCallback", &cthulhu::PyAligner::setAlignCallback);

  py::class_<cthulhu::PyImageBuffer>(m, "ImageBuffer", py::buffer_protocol())
      .def_buffer([](cthulhu::PyImageBuffer& b) -> py::buffer_info {
        return py::buffer_info(
            b.data(),
            sizeof(uint8_t),
            py::format_descriptor<uint8_t>::format(),
            2,
            {b.height(), b.width()},
            {sizeof(uint8_t) * b.stride(), sizeof(uint8_t)});
      })
      .def(
          "__len__",
          [](const cthulhu::PyImageBuffer& img) -> size_t { return img.width() * img.height(); })
      .def_property_readonly("width", &cthulhu::PyImageBuffer::width)
      .def_property_readonly("height", &cthulhu::PyImageBuffer::height);

  py::class_<cthulhu::PerformanceSummary>(m, "PerformanceSummary")
      .def_readonly("min_runtime", &cthulhu::PerformanceSummary::minRuntime)
      .def_readonly("mean_runtime", &cthulhu::PerformanceSummary::meanRuntime)
      .def_readonly("max_runtime", &cthulhu::PerformanceSummary::maxRuntime)
      .def_readonly("total_runtime", &cthulhu::PerformanceSummary::totalRuntime)
      .def_readonly("num_calls", &cthulhu::PerformanceSummary::numCalls)
      .def_readonly("num_samples_dropped", &cthulhu::PerformanceSummary::numSamplesDropped);

  py::enum_<cthulhu::BufferType>(m, "BufferType", py::arithmetic())
      .value("NULL_BUFFER", cthulhu::BufferType::NULL_BUFFER)
      .value("CPU", cthulhu::BufferType::CPU)
      .value("GPU", cthulhu::BufferType::GPU);
}
} // namespace core
} // namespace cthulhu
