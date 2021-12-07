// Copyright 2004-present Facebook. All Rights Reserved.

#include <labgraph/bindings.h>

#include <labgraph/Node.h>
#include <pybind11/stl.h>

#include <cthulhu/Framework.h>

namespace py = pybind11;

namespace labgraph {

void bindings(py::module_& m) {
  m.doc() = "Labgraph C++: C++ nodes for Labgraph";

  py::class_<Node>(m, "Node")
      .def("setup", &Node::setup)
      .def("cleanup", &Node::cleanup)
      .def("run", &Node::run)
      .def("_bootstrap", &Node::bootstrap)
      .def_property_readonly("topics", &Node::getTopics);

  py::class_<NodeTopic>(m, "NodeTopic")
      .def(py::init<std::string, cthulhu::StreamID>(), py::arg("topic_name"), py::arg("stream_id"))
      .def_readonly("topic_name", &NodeTopic::topicName)
      .def_readonly("stream_id", &NodeTopic::streamID);

  py::class_<NodeBootstrapInfo>(m, "NodeBootstrapInfo")
      .def(py::init<std::vector<NodeTopic>>(), py::arg("topics"))
      .def_readonly("topics", &NodeBootstrapInfo::topics);
}

} // namespace labgraph

PYBIND11_MODULE(labgraph_cpp, m) {
  labgraph::bindings(m);

  py::cpp_function cleanup_callback([](py::handle weakref) {
    cthulhu::Framework::instance().cleanup();
    weakref.dec_ref();
  });

  // Call cleanup with a weakref to a sentinel object on the bindings via a callback.
  // This ensures cleanup happens early enough for the Vulkan API to still be loaded.
  m.def("_sentinel", []() -> void {});
  (void)py::weakref(m.attr("_sentinel"), cleanup_callback).release();
}
