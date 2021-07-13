#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import dataclasses
import enum
import multiprocessing as mp
import pickle
import socket
import subprocess
import tempfile
import time
from multiprocessing import managers
from typing import Callable, Dict, Optional, Sequence, Set, Tuple, Union

import psutil

from ..util.logger import get_logger
from ..util.random import random_string
from .launch import launch


logger = get_logger(__name__)

MONITOR_SLEEP_TIME = 0.01
DEFAULT_STARTUP_PERIOD = 60
DEFAULT_SHUTDOWN_PERIOD = 30
AUTH_KEY_LENGTH = 16


class ProcessPhase(enum.Enum):
    """
    Describes the current running state of a process managed by a `ProcessManager`.
    """

    STARTING = enum.auto()
    READY = enum.auto()
    RUNNING = enum.auto()
    STOPPING = enum.auto()
    TERMINATED = enum.auto()


class ProcessFailureType(enum.Enum):
    CRASH = enum.auto()
    EXCEPTION = enum.auto()
    HANG = enum.auto()


class ProcessManagerException(RuntimeError):
    """
    Raised when something goes wrong when running a `ProcessManager`.
    """

    def __init__(
        self,
        failures: Dict[str, Optional[ProcessFailureType]],
        exceptions: Dict[str, Optional[str]],
        phases: Dict[str, ProcessPhase],
    ) -> None:
        self._failures = failures
        self._exceptions = exceptions
        self._phases = phases
        super().__init__(self.message)

    @property
    def failures(self) -> Dict[str, Optional[ProcessFailureType]]:
        return self._failures

    @property
    def exceptions(self) -> Dict[str, Optional[str]]:
        return self._exceptions

    @property
    def message(self) -> str:
        msg = "Some managed processes failed:\n"
        for process_name in self._failures.keys():
            msg += self._message_for_failure(process_name) + "\n"
        return msg

    def _message_for_failure(self, process_name: str) -> str:
        return f"- {process_name}: " + {
            None: "Terminated normally",
            ProcessFailureType.CRASH: "Crashed (terminated unexpectedly)",
            ProcessFailureType.EXCEPTION: (
                f"Raised an exception: {self._exceptions[process_name]}"
            ),
            ProcessFailureType.HANG: (
                "Hanged (stopped responding) while in phase "
                f"{self._phases[process_name].name}"
            ),
        }[self._failures[process_name]]


@dataclasses.dataclass
class ProcessManagerServerInfo:
    port: int
    auth_key: bytes = dataclasses.field(
        default_factory=lambda: random_string(AUTH_KEY_LENGTH).encode("ascii")
    )
    host: str = "127.0.0.1"

    @property
    def address(self) -> Tuple[str, int]:
        return (self.host, self.port)


class ProcessManagerState:
    """
    Holds state for all the processes managed by a `ProcessManager`. Thread-safe.

    Args:
        process_names: The names of all the processes being managed.
    """

    # Argument passed to subprocesses so they can find the shared state
    SUBPROCESS_ARG = "process-manager-state-file"

    _server_info: Optional[ProcessManagerServerInfo] = None
    _manager: Optional[mp.managers.SyncManager] = None
    _manager_started = False

    def __init__(self, process_names: Set[str], manager_name: str) -> None:
        # Start the `mp.Manager` if it is not started
        if not self.__class__._manager_started:
            self.__class__._server_info = ProcessManagerServerInfo(
                port=self.__class__._get_free_tcp_port()
            )
            self.__class__._manager = mp.managers.SyncManager(
                authkey=self.__class__._server_info.auth_key,
                address=self.__class__._server_info.address,
            )
            self.__class__._manager.start()
            self.__class__._manager_started = True

        assert self._manager is not None

        self._manager_name = manager_name
        process_names = set(process_names).union({manager_name})

        # Basic state of all managed processes
        self._phases = self._manager.dict(
            {process_name: ProcessPhase.STARTING for process_name in process_names}
        )
        self._exceptions: Dict[str, Optional[str]] = self._manager.dict(
            {process_name: None for process_name in process_names}
        )

        # Synchronizes access to _phases and _exceptions
        self.lock = self._manager.RLock()

    def get_all(self) -> Dict[str, ProcessPhase]:
        """
        Returns the current running state for all managed processes.
        """
        with self.lock:
            return {**self._phases}

    def get(self, name: str) -> ProcessPhase:
        """
        Returns the current running state for the managed process with the given name.

        Args:
            name: The name of the managed process.
        """
        return self._phases[name]

    def update(self, name: str, phase: ProcessPhase) -> None:
        """
        Updates the current running state for the managed process with the given name.

        Args:
            name: The name of the managed process.
            phase: The new running state.
        """
        with self.lock:
            old_phase = self._phases[name]
            logger.debug(f"{name}:updated state:{old_phase.name} -> {phase.name}")
            assert phase.value > old_phase.value
            self._phases[name] = phase

    def get_exception(self, name: str) -> Optional[str]:
        """
        Gets the description of the exception that the managed process with the given
        name raised, if any.

        Args:
            name: The name of the managed process.
        """
        return self._exceptions[name]

    def set_exception(self, name: str, exception_desc: str) -> None:
        """
        Sets the current exception for the managed process with the given name.

        Args:
            name: The name of the managed process.
            exception_desc:
                A string description of the exception that was thrown by the managed
                process.
        """
        with self.lock:
            assert self.get_exception(name) is None
            self._exceptions[name] = exception_desc

    @property
    def has_exception(self) -> bool:
        """
        Returns true if an exception was raised in any process.
        """
        with self.lock:
            return any(exception is not None for exception in self._exceptions.values())

    @classmethod
    def load(cls, filename: str) -> "ProcessManagerState":
        """
        Loads a saved `ProcessManagerState` from a file.

        Args:
            filename: The filename to read the state from.
        """
        # See https://bugs.python.org/msg214582 for more information on why we use auth
        # keys here.
        with open(filename, "rb") as state_file:
            # Unpickle the outer layer
            result = pickle.load(state_file)
            assert isinstance(result, tuple)
            # The outer layer should contain an auth key as well as the "real" bytes
            server_info, state_bytes = result
            assert isinstance(server_info, ProcessManagerServerInfo)
            assert isinstance(state_bytes, bytes)
            # Unpickling `mp.Manager` proxy objects (`_phases` and `_exceptions`)
            # requires us to set the correct auth key. We do so temporarily to avoid
            # contaminating global state.
            old_auth_key = mp.current_process().authkey
            mp.current_process().authkey = server_info.auth_key
            state = pickle.loads(state_bytes)
            assert isinstance(state, ProcessManagerState)
            mp.current_process().authkey = old_auth_key
            return state

    def dump(self, filename: str) -> None:
        """
        Dumps this `ProcessManagerState` to a file.

        Args:
            filename: The filename to dump to.
        """
        # See https://bugs.python.org/msg214582 for more information on why we use auth
        # keys here.
        with open(filename, "wb") as state_file:
            # We pickle twice: first we pickle the state itself, and then we pickle the
            # auth key with the pickled bytes. The reason is we will need this auth key
            # in the child process in order to unpickle the state bytes.
            state_bytes = pickle.dumps(self)
            pickle.dump((self.__class__._server_info, state_bytes), state_file)

    def get_overall(self) -> ProcessPhase:
        """
        Returns the overall phase of all managed processes.
        """
        return self._phases[self._manager_name]

    @classmethod
    def _get_free_tcp_port(cls) -> int:
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind(("", 0))
        addr, port = tcp.getsockname()
        tcp.close()
        return int(port)


@dataclasses.dataclass(frozen=True)
class ProcessInfo:
    """
    Describes a process to be run by a `ProcessManager`.

    Args:
        module: The Python module to run in the child process.
        args: Any arguments to pass to the child process. Empty by default.
        name:
            The name of the child process. If not provided, an integer counter will be
            used.
    """

    module: str
    args: Tuple[str, ...] = dataclasses.field(default_factory=tuple)
    name: Optional[str] = None


class ProcessManager:
    """
    Class for managing several process. The `ProcessManager` handles starting all the
    processes, sharing state between them, and terminating the processes if anything
    goes wrong (i.e., if a crash, an exception, or a hang occurs).

    Args:
        processes:
            A list of `ProcessInfo` objects describing processes to run. Each process
            will receive a --process-manager-state-file option with a filename that
            it should load a `ProcessManagerState` from. Then it is expected to keep
            that state object up-to-date on its status.
        name:
            The name of this process manager. This will be used to track the state of
            the overall graph in `ProcessManagerState`.
        startup_period:
            The time, in seconds, that each process has to start running. If a process
            exceeds this time, the `ProcessManager` will consider this an erroneous
            state and stop all the processes.
        shutdown_period:
            The time, in seconds, that each process has to shut down. If a process
            exceeds this time, the `ProcessManager` will consider this a hang and stop
            all the processes.
    """

    def __init__(
        self,
        processes: Sequence[ProcessInfo],
        name: Optional[str] = None,
        startup_period: float = DEFAULT_STARTUP_PERIOD,
        shutdown_period: float = DEFAULT_SHUTDOWN_PERIOD,
    ) -> None:
        self._name = name or self.__class__.__name__
        self._startup_period = startup_period
        self._shutdown_period = shutdown_period

        # Index the `ProcessInfo` objects by name, and fill in the names for any without
        # names using an integer counter
        self._process_info: Dict[str, ProcessInfo] = {}
        process_counter = 0
        for process_info in processes:
            if process_info.name is None:
                while str(process_counter) in self._process_info.keys():
                    process_counter += 1
                process_info = dataclasses.replace(
                    process_info, name=str(process_counter)
                )
            if process_info.name in self._process_info.keys():
                raise ValueError(
                    f"{self.__class__.__name__} got multiple processes named "
                    f"{process_info.name}"
                )
            assert process_info.name is not None
            assert process_info.name != self._name
            self._process_info[process_info.name] = process_info

        # Initiatialize state (this will be shared between processes via `mp.Manager`)
        self._state = ProcessManagerState(set(self._process_info.keys()), self._name)

        # Write the state information to disk so that other processes can access it
        self._state_file = tempfile.NamedTemporaryFile(delete=False)
        self._state_file.close()
        self._state.dump(self._state_file.name)

        # Runtime state for the manager
        self._processes: Dict[str, subprocess.Popen] = {}  # type: ignore
        self._start_time: Optional[float] = None

        self._manager_exception: Optional[BaseException] = None
        self._hanged_processes: Set[str] = set()
        self._crashed_processes: Set[str] = set()

    def run(self) -> None:
        """
        Runs the `ProcessManager`. This starts all the processes and blocks until they
        all terminate. This may raise an exception if a crash, an exception, or a hang
        occurred in the processes that were started.
        """
        try:
            self._start_processes()
            # Because process startup time can be variable, start the timer for process
            # startup after all processes are staretd
            self._start_time = time.perf_counter()
            self._wait_for_startup_phase(ProcessPhase.READY)
            self._wait_for_startup_phase(ProcessPhase.RUNNING)
            self._monitor()
        except BaseException as e:
            self._manager_exception = e
            self._terminate_gracefully()
        finally:
            self._raise_exception()

    def _start_processes(self) -> None:
        """
        Starts all the processes.
        """
        for process_info in self._process_info.values():
            # `launch` launches a child process, resilient to PEX environments
            assert process_info.name is not None
            self._processes[process_info.name] = launch(
                process_info.module,
                process_info.args
                + (
                    f"--{ProcessManagerState.SUBPROCESS_ARG}",
                    self._state_file.name,
                    "--process-name",
                    process_info.name,
                ),
            )

    def _wait_for_startup_phase(self, target_phase: ProcessPhase) -> None:
        """
        Waits for all processes to enter the same phase during startup. Kills all
        processes if they crash, raise, or hang.
        """
        if self._state.get(self._name).value >= target_phase.value:
            self._terminate_gracefully()
            return
        should_terminate = False  # Flag that can be set to kill the manager
        logger.debug(
            f"{self._name}:waiting for all processes to be {target_phase.name}"
        )
        while True:
            with self._state.lock:
                # Check if any process has crashed
                self._check_crashed_processes()
                if len(self._crashed_processes) > 0:
                    should_terminate = True

                # Check if any process raised an exception
                if self._state.has_exception:
                    should_terminate = True

                phases = self._state.get_all()

            # Stop waiting if all the processes have entered the right state
            if all(
                phase.value >= target_phase.value
                for name, phase in phases.items()
                if name != self._name
            ):
                overall_phase = ProcessPhase(
                    min(
                        phase.value
                        for name, phase in phases.items()
                        if name != self._name
                    )
                )
                if self._state.get_overall() != overall_phase:
                    self._state.update(self._name, overall_phase)
                break

            # Check if any processes took too long to enter the state
            slow_processes = {
                process_name: phase
                for process_name, phase in phases.items()
                if phase.value < target_phase.value and process_name != self._name
            }
            current_time = time.perf_counter()
            assert self._start_time is not None
            if (
                current_time - self._start_time >= self._startup_period
                and len(slow_processes) > 0
            ):
                error = (
                    f"{self._name}:modules took too long to be {target_phase.name}:\n"
                )
                for name, phase in slow_processes.items():
                    error += f"- {name}: {phase.name}\n"
                    self._hanged_processes.add(name)
                logger.error(error)

                should_terminate = True

            if should_terminate:
                break

            time.sleep(MONITOR_SLEEP_TIME)

        # Terminate if the termination flag was set
        if should_terminate:
            self._terminate_gracefully()
            return

        logger.debug(f"{self._name}:processes are all {target_phase.name}")

    def _monitor(self) -> None:
        """
        Monitors the running processes for any change in their state.
        """
        if self._state.get_overall().value >= ProcessPhase.STOPPING.value:
            return
        logger.debug(f"{self._name}:monitoring running processes")
        should_terminate = False
        while True:
            with self._state.lock:
                # If any process is stopping, stop all managed processes
                for process_name, phase in self._state._phases.items():
                    if phase.value >= ProcessPhase.STOPPING.value:
                        logger.debug(f"{self._name}:{process_name} stopping")
                        should_terminate = True

                # Check if any process has crashed
                self._check_crashed_processes()
                if len(self._crashed_processes) > 0:
                    should_terminate = True

                # Check if any process has raised an exception
                if self._state.has_exception:
                    should_terminate = True
                    break

            if should_terminate:
                break

            time.sleep(MONITOR_SLEEP_TIME)
        logger.debug(f"{self._name}:monitoring complete")
        if should_terminate:
            self._terminate_gracefully()

    def _raise_exception(self) -> None:
        """
        Raises an exception based on the information collected while the managed
        processes were running.
        """
        if self._manager_exception is not None:
            raise self._manager_exception
        with self._state.lock:
            if (
                all(exception is None for exception in self._state._exceptions.values())
                and len(self._hanged_processes) == 0
                and len(self._crashed_processes) == 0
            ):
                return
            raise ProcessManagerException(
                failures={
                    process_name: ProcessFailureType.EXCEPTION
                    if self._state._exceptions[process_name] is not None
                    else ProcessFailureType.HANG
                    if process_name in self._hanged_processes
                    else ProcessFailureType.CRASH
                    if process_name in self._crashed_processes
                    else None
                    for process_name in self._process_info.keys()
                },
                exceptions={**self._state._exceptions},
                phases=self._state.get_all(),
            )

    def _terminate_gracefully(self) -> None:
        """
        Terminates the managed processes gratefully.
        """
        # Short circuit if already terminated
        if self._state.get(self._name) == ProcessPhase.TERMINATED:
            return

        logger.debug(f"{self._name}:terminating gracefully")

        with self._state.lock:
            # Set the manager's state to STOPPING. This is the signal that managed
            # processes must use - they are expected to then stop and terminate
            # themselves. This makes for a graceful termination.
            if self._state.get(self._name) != ProcessPhase.STOPPING:
                self._state.update(self._name, ProcessPhase.STOPPING)

        terminate_start = time.perf_counter()
        # Wait for all processes to terminate
        while True:
            if len(self._get_dead_processes()) == len(self._processes):
                with self._state.lock:
                    self._state.update(self._name, ProcessPhase.TERMINATED)

                    # Check if any processes crashed while stopping
                    if self._state.get_exception(self._name) is None:
                        self._check_crashed_processes()

                logger.debug(f"{self._name}:terminated gracefully")
                return

            # Check if the termination has exceeded the shutdown period
            current_time = time.perf_counter()
            if current_time - terminate_start >= self._shutdown_period:
                break
            time.sleep(MONITOR_SLEEP_TIME)

        for process_name in set(self._processes.keys()).difference(
            self._get_dead_processes()
        ):
            self._hanged_processes.add(process_name)
        logger.warning(f"{self._name}:graceful termination timed out")
        # No more Mr. Nice Guy; terminate the processes forcibly
        self._terminate_forcibly()

    def _terminate_forcibly(self) -> None:
        # Short circuit if already terminated
        if self._state.get(self._name) == ProcessPhase.TERMINATED:
            return

        logger.warning(f"{self._name}:terminating forcibly")
        with self._state.lock:
            if self._state.get(self._name) != ProcessPhase.STOPPING:
                self._state.update(self._name, ProcessPhase.STOPPING)

        # Murder all the processes
        for name, process in self._processes.items():
            if process.poll() is None:
                proc = psutil.Process(process.pid)
                for child in proc.children(recursive=True):
                    child.kill()
                proc.kill()
                logger.warning(f"{name}: terminated forcibly")

        with self._state.lock:
            self._state.update(self._name, ProcessPhase.TERMINATED)

    def _get_dead_processes(self) -> Set[str]:
        """
        Returns all processes that are no longer alive.
        """
        return {
            process_name
            for process_name, process in self._processes.items()
            if process.poll() is not None
        }

    def _check_crashed_processes(self) -> None:
        """
        Checks for crashed processes. Crashed processes are dead processes whose final
        phase was not TERMINATED.
        """
        with self._state.lock:
            dead_processes = self._get_dead_processes()
            crashed_processes = {
                name
                for name in dead_processes
                if self._state.get(name) != ProcessPhase.TERMINATED
            }
            if len(crashed_processes) > 0:
                error = f"{self._name}:modules crashed:\n"
                for process_name in crashed_processes:
                    self._crashed_processes.add(process_name)
                    error += f"- {process_name}\n"
                logger.error(error)
