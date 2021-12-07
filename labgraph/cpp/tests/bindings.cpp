// Copyright 2004-present Facebook. All Rights Reserved.

#include <labgraph/bindings.h>
#include <pybind11/pybind11.h>
#include "MyCPPSink.h"
#include "MyCPPSource.h"

namespace py = pybind11;

PYBIND11_MODULE(MyCPPNodes, m) {
  m.doc() = "Labgraph C++: MyCPPNodes unit test";

  std::vector<std::string> sourceTopics = {"A"};
  labgraph::bindNode<MyCPPSource>(m, "MyCPPSource", sourceTopics)
      .def(py::init())
      .def_readonly_static("NUM_SAMPLES", &MyCPPSource::kNumSamples);

  std::vector<std::string> sinkTopics = {"B"};
  labgraph::bindNode<MyCPPSink>(m, "MyCPPSink", sinkTopics)
      .def(py::init<const std::string&>(), py::arg("filename"));
}
