#include "ClockManagerIPC.h"

#include <cassert>

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

namespace cthulhu {

const std::shared_ptr<ControllableClockInterface> ClockManagerIPC::controlClock(
    const std::string& contextName) {
  if (!data_->clockOwnerContext.empty() &&
      contextName.compare(data_->clockOwnerContext.c_str()) == 0) {
    auto control_clock = std::dynamic_pointer_cast<ControllableClockIPC>(clock());
    control_clock->setControlLocal();
    return control_clock;
  }
  XR_LOGCW(
      "Cthulhu", "Could not provide a controllable clock to non-owning context {}", contextName);
  return std::shared_ptr<ControllableClockIPC>();
}

const std::shared_ptr<ClockInterface> ClockManagerIPC::clock() {
  if (state_ == ClockManagerState::UNKNOWN) {
    return std::shared_ptr<ClockInterface>();
  }
  if (!clock_handle_) {
    if (state_ == ClockManagerState::REAL) {
      clock_handle_ = std::make_shared<ClockIPC>(&data_->clock);
    } else {
      clock_handle_ = std::make_shared<ControllableClockIPC>(&data_->clock);
    }
  }
  return clock_handle_;
}

void ClockManagerIPC::setClockAuthority(bool simTime, const std::string& authorizedContext) {
  ScopedLockIPC lock(data_->lock);
  if (!data_->clockOwnerContext.empty() &&
      authorizedContext.compare(data_->clockOwnerContext.c_str()) != 0) {
    XR_LOGE("Clock authority context mismatch with shared memory.");
  }
  data_->clockOwnerContext = authorizedContext.c_str();
  ClockManagerState newState = simTime ? ClockManagerState::SIM : ClockManagerState::REAL;
  if (data_->state != ClockManagerState::UNKNOWN && data_->state != newState) {
    XR_LOGE("Clock authority type mismatch with shared memory.");
  }
  data_->state = newState;
  state_ = newState;
}

ClockManagerIPC::ClockManagerIPC(ManagedSHM* shm) : shm_(shm) {
  data_ = shm_->find_or_construct<ClockManagerIPCData>("ClockManager")(shm_->get_segment_manager());

  if (data_ == nullptr) {
    auto str = "Failed to open clock manager in shared memory.";
    XR_LOGE("{}", str);
    throw std::runtime_error(str);
  }

  // We're using an atomic in shared memory... it needs to be lock free.
  // The C++ standard does not guarantee this, so its up to the compiler.
  if (!std::atomic_is_lock_free(&data_->clock.latestTime)) {
    auto str = "Cthulhu IPC requires that atomic<double> be implemented lock-free.";
    XR_LOGE("{}", str);
    throw std::runtime_error(str);
  }

  ScopedLockIPC lock(data_->lock);
  data_->reference_count++;
  state_ = data_->state;
}

bool ClockManagerIPC::nuke(ManagedSHM* shm) {
  shm->destroy<ClockManagerIPCData>("ClockManager");
  return true;
}

ClockManagerIPC::~ClockManagerIPC() {
  if (clock_handle_.use_count() > 1 && log_enabled_) {
    XR_LOGE("ClockManagerIPC - cleaning up while references to the clock are still out there!");
  }

  clock_handle_ = std::shared_ptr<ClockIPC>();

  if (data_) {
    ScopedLockIPC lock(data_->lock);
    data_->reference_count--;
    if (data_->reference_count == 0 || force_clean_) {
      data_->reference_count = 0;
      data_->clockOwnerContext.clear();
      data_->state = ClockManagerState::UNKNOWN;
      data_->clock.reset();
      if (log_enabled_) {
        XR_LOGD("Cleaning up ipc clock manager.");
      }
    } else if (log_enabled_) {
      XR_LOGD("Not cleaning ipc clock manager, still references: {}", data_->reference_count);
    }
  }
}

} // namespace cthulhu
