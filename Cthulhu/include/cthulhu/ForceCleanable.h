#pragma once

namespace cthulhu {

class ForceCleanable {
 public:
  virtual ~ForceCleanable() = default;
  virtual inline void forceClean() {
    force_clean_ = true;
  }

 protected:
  bool force_clean_ = false;
};

} // namespace cthulhu
