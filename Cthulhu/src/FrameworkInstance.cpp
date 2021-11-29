#include <cthulhu/Framework.h>

#if defined(_WIN32)
#if defined(__clang__)
#define DLLEXPORT __attribute__((visibility("default")))
#else
#define DLLEXPORT __declspec(dllexport)
#endif
#else
#define DLLEXPORT
#endif

namespace cthulhu {

class FrameworkInstance {
 public:
  Framework framework;
};

extern DLLEXPORT Framework* getFramework() {
  static FrameworkInstance finstance;
  return &(finstance.framework);
}

DLLEXPORT SharedRawDynamicArray makeSharedRawDynamicArray(size_t count) {
  return std::shared_ptr<RawDynamic<>>(
      new RawDynamic<>[count](), std::default_delete<RawDynamic<>[]>());
}

DLLEXPORT CpuBuffer makeSharedCpuBuffer(size_t count) {
  return CpuBuffer(new uint8_t[count](), std::default_delete<uint8_t[]>());
}

} // namespace cthulhu
