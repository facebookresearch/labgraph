// Copyright 2004-present Facebook. All Rights Reserved.

#include "AuditorIPC.h"

#define DEFAULT_LOG_CHANNEL "Cthulhu"
#include <logging/Log.h>

#ifndef _WIN32
#include <signal.h>
#endif

namespace cthulhu {

#ifdef _WIN32
AuditorIPC::Process::Process() : processId_{GetCurrentProcessId()} {}

bool AuditorIPC::Process::isSelf() const {
  return processId_ == GetCurrentProcessId();
}

bool AuditorIPC::Process::isAlive() const {
  DWORD exitCode;
  bool alive = false;
  HANDLE hProcess = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, processId_);
  if (hProcess != NULL) {
    alive = GetExitCodeProcess(hProcess, &exitCode) && exitCode == STILL_ACTIVE;
    CloseHandle(hProcess);
  }
  return alive;
}
#else
AuditorIPC::Process::Process() : pid_{getpid()} {}

bool AuditorIPC::Process::isSelf() const {
  return pid_ == getpid();
}

bool AuditorIPC::Process::isAlive() const {
  return kill(pid_, 0) >= 0;
}
#endif

} // namespace cthulhu
