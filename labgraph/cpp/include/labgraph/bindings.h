// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include <labgraph/Node.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace labgraph {
void bindings(pybind11::module&);

template <typename T>
pybind11::class_<T, labgraph::Node> bindNode(
    pybind11::module& m,
    const std::string& pythonName,
    const std::vector<std::string>& topicNames) {
  auto result = pybind11::class_<T, labgraph::Node>(m, pythonName.c_str());
  result = result.def_property_readonly_static(
      "topic_names", [topicNames](pybind11::object /* self */) { return topicNames; });
  return result;
}

} // namespace labgraph
