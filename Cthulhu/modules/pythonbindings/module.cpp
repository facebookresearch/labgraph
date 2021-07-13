// Copyright 2004-present Facebook. All Rights Reserved.

#ifndef CTHULHU_EXTERNAL
#include <cthulhu/bindings/common_types.h>
#endif

#include <cthulhu/bindings/core.h>
#include <pybind11/pybind11.h>

#ifndef CTHULHU_EXTERNAL
#include <xr_init/xrinit_binding_registration.h>
#endif

namespace py = pybind11;

PYBIND11_MODULE(cthulhubindings, m) {
  cthulhu::core::bindings(m);

#ifndef CTHULHU_EXTERNAL
  cthulhu::common_types::bindings(m);
  log_utils::registerBindingsForXRInit(m);

  m.def(
      "compute_sample_size",
      [](const cthulhu::PyStreamConfig& cfg, const std::string& typeName) -> uint32_t {
        if (auto dispatcher =
                cthulhu::common_types::computeSampleSizeDispatch(cfg.getConfig(), typeName);
            dispatcher) {
          return dispatcher()->computeSampleSize();
        } else {
          throw std::runtime_error(
              "The computeSampleSize associated with type " + typeName + " is not available");
        }
      });

  py::cpp_function cleanup_callback([](py::handle weakref) {
    cthulhu::Framework::instance().cleanup();
    weakref.dec_ref();
  });

  // Call cleanup with a weakref to a sentinel object on the bindings via a callback.
  // This ensures cleanup happens early enough for the Vulkan API to still be loaded.
  m.def("_sentinel", []() -> void {});
  (void)py::weakref(m.attr("_sentinel"), cleanup_callback).release();
#endif
}
