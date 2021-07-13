# C++ Interoperability

Sometimes, Python just isn't fast enough to be able to process real-time signals within an acceptable latency bound. (Or, it's too much effort to tune Python to do so.) In these cases, we may want to drop down to C++ to implement some real-time processing in a more performant manner.



LabGraph comes with a `labgraph_cpp` library which allows us to define nodes directly in C++. Then, with the help of [pybind11](https://github.com/pybind/pybind11), we can embed that node in a LabGraph graph just as we would a Python node.

```
// MyCPPSource.h
#pragma once
#include <labgraph/Node.h>
class MyCPPSource : public labgraph::Node {
 public:
  std::vector<std::string> getTopics() const;
  std::vector<labgraph::PublisherInfo> getPublishers();
  void mainPublisher();
  static constexpr int const& kNumSamples = 10;
  static constexpr double const& kPublishRate = 5.0;
};
```


```
// MyCPPSource.cpp
#include "MyCPPSource.h"
#include "TestSample.h"
std::vector<std::string> MyCPPSource::getTopics() const {
  return {"A"};
}
std::vector<labgraph::PublisherInfo> MyCPPSource::getPublishers() {
  return {{{"A"}, [this]() { mainPublisher(); }}};
}
void MyCPPSource::mainPublisher() {
  // Publisher that sends 10 messages with a single int in each one
  const double publish_sleep = 1.0 / kPublishRate;
  for (uint32_t i = 0; i < kNumSamples; i++) {
    TestSample sample;
    sample.value = i;
    publish<TestSample>("A", sample);
    std::this_thread::sleep_for(std::chrono::duration<double>(publish_sleep));
  }
}
```
In the header and implementation above, we are defining `MyCPPSource`, which is a LabGraph C++ node that publishes to a single topic, A. Its number of samples and publish rate is fixed in this example, but these could be made configurable with a configuration object. `TestSample` as defined in TestSample.h is a Cthulhu sample type; see the [Cthulhu documentation](cthulhu) for more details on this.



```
#include <labgraph/bindings.h>
#include <pybind11/pybind11.h>
#include "MyCPPSource.h"

namespace py = pybind11;

PYBIND11_MODULE(MyCPPNodes, m) {
  std::vector<std::string> sourceTopics = {"A"};
  labgraph::bindNode<MyCPPSource>(m, "MyCPPSource", sourceTopics)
      .def(py::init())
      .def_readonly_static("NUM_SAMPLES", &MyCPPSource::kNumSamples);
}
```


Here we use pybind11 to create Python bindings for the node. Note the use of the `labgraph::bindNode` function; this creates a class binding with methods that LabGraph uses to identify information about the node, and then it returns the class binding for you to use like any other pybind11 binding.



Finally, we can use `MyCPPSource` in a LabGraph graph:



```
from MyCPPNodes import MyCPPSource
class MyGraph(df.Graph):
  CPP_SOURCE: MyCPPSource
  ...
```
