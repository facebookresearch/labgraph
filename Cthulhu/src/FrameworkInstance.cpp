// Copyright 2004-present Facebook. All Rights Reserved.

#include <cthulhu/Framework.h>

#ifdef _WIN32
#define DLLEXPORT __declspec(dllexport)
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

} // namespace cthulhu
