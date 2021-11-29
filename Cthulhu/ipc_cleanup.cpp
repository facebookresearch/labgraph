// Copyright 2004-present Facebook. All Rights Reserved.

#define DEFAULT_LOG_CHANNEL "CthulhuIPCClean"
#include <cthulhu/Framework.h>
#include <logging/Log.h>

int main(int argc, char** argv) {
  for (int argIdx = 0; argIdx < argc; argIdx++) {
    if ("--hard" == std::string_view(argv[argIdx])) {
      XR_LOGW("Nuking Cthulhu shared memory. This will reset Cthulhu for all users.");
      if (!cthulhu::Framework::nuke()) {
        XR_LOGW("Failed to nuke Cthulhu shared memory.");
        return 1;
      } else {
        XR_LOGI("Nuked Cthulhu shared memory.");
        return 0;
      }
    }
  }
  XR_LOGW("Cleaning up Cthulhu shared memory.");
  cthulhu::Framework::instance().cleanup(true);
  XR_LOGI("Cleaned up Cthulhu shared memory.");
  return 0;
}
