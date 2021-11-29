#pragma once

namespace cthulhu {

class LogDisabling {
 public:
  virtual ~LogDisabling() = default;
  virtual inline void disableLogging() {
    log_enabled_ = false;
  }

 protected:
  bool log_enabled_ = true;
};

} // namespace cthulhu
