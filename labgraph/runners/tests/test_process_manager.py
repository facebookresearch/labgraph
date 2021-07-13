#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import enum
import functools
import sys
import time
from typing import Optional

import click
import pytest

from ...util.testing import local_test
from ..process_manager import (
    ProcessFailureType,
    ProcessInfo,
    ProcessManager,
    ProcessManagerException,
    ProcessManagerState,
    ProcessPhase,
)


TEST_STARTUP_PERIOD = 5
TEST_SHUTDOWN_PERIOD = 3
PROCESS_WAIT_TIME = 0.1
PROCESS_SLEEP_TIME = 0.01


class DummyException(Exception):
    """
    Dummy exception for tests to raise.
    """

    pass


class ShutdownBehavior(enum.Enum):
    """
    A shutdown behavior that `proc` can observe.
    """

    NORMAL = enum.auto()
    CRASH = enum.auto()
    EXCEPTION = enum.auto()
    HANG = enum.auto()


def proc(
    state: ProcessManagerState,
    name: str,
    manager_name: str,
    shutdown: ShutdownBehavior,
    last_phase: ProcessPhase = ProcessPhase.TERMINATED,
) -> None:
    """
    A minimal version of a process managed by a `ProcessManager`. Used for testing the
    `ProcessManager`. The process simply updates its phase and sleeps.

    Args:
        state: The `ProcessManager`'s state.
        name: The name of the process.
        manager_name: The name of the `ProcessManager`.
        shutdown:
            The shutdown behavior that this process will observe:
            - `ShutdownBehavior.NORMAL`: go through all phases and terminate normally.
            - `ShutdownBehavior.CRASH`: exit the entire process suddenly at a certain
              phase.
            - `ShutdownBehavior.EXCEPTION`: raise an exception at a certain phase.
            - `ShutdownBehavior.HANG: hang at a certain phase.
        last_phase:
            The last phase that `proc` will enter. This must be
            `ProcessPhase.TERMINATED` if the shutdown behavior is normal.
    """
    assert shutdown != ShutdownBehavior.NORMAL or last_phase == ProcessPhase.TERMINATED
    last_phase_changed_at = time.perf_counter()

    while True:
        time.sleep(PROCESS_SLEEP_TIME)

        # If the manager is stopping, set this process to be stopping
        with state.lock:
            if (
                state.get(manager_name) == ProcessPhase.STOPPING
                and state.get(name) != ProcessPhase.STOPPING
            ):
                state.update(name, ProcessPhase.STOPPING)
                last_phase_changed_at = time.perf_counter()

                # Leave the sleep loop if we are now in the last phase
                if ProcessPhase.STOPPING.value >= last_phase.value:
                    break

        # Transition to the next phase if we have slept for long enough
        current_time = time.perf_counter()
        if current_time - last_phase_changed_at > PROCESS_WAIT_TIME:
            current_phases = state.get_all()
            current_phase = current_phases[name]
            if (
                current_phase == ProcessPhase.READY
                and current_phases[manager_name].value < ProcessPhase.READY.value
            ):
                continue
            new_phase = {
                ProcessPhase.STARTING: ProcessPhase.READY,
                ProcessPhase.READY: ProcessPhase.RUNNING,
                ProcessPhase.RUNNING: ProcessPhase.STOPPING,
                ProcessPhase.STOPPING: ProcessPhase.TERMINATED,
            }[current_phase]
            state.update(name, new_phase)
            last_phase_changed_at = time.perf_counter()

            # Leave the sleep loop if we are now in the last phase
            if new_phase.value >= last_phase.value:
                break

    if shutdown == ShutdownBehavior.EXCEPTION:
        # Update the state with a dummy exception, then stop
        state.set_exception(name, repr(DummyException()))
        with state.lock:
            if state.get(name) != ProcessPhase.STOPPING:
                state.update(name, ProcessPhase.STOPPING)
        time.sleep(PROCESS_WAIT_TIME)
        state.update(name, ProcessPhase.TERMINATED)
        return
    elif shutdown == ShutdownBehavior.HANG:
        # Hang forever; the `ProcessManager` should then kill this process
        while True:
            time.sleep(PROCESS_SLEEP_TIME)


@local_test
def test_normal() -> None:
    """
    Tests that we can run multiple processes that terminate normally.
    """
    manager = ProcessManager(
        processes=(
            ProcessInfo(
                module=__name__,
                name="proc1",
                args=("--manager-name", "test_manager", "--shutdown", "NORMAL"),
            ),
            ProcessInfo(
                module=__name__,
                name="proc2",
                args=("--manager-name", "test_manager", "--shutdown", "NORMAL"),
            ),
        ),
        name="test_manager",
        startup_period=TEST_STARTUP_PERIOD,
        shutdown_period=TEST_SHUTDOWN_PERIOD,
    )

    manager.run()


@pytest.mark.parametrize(
    "crash_phase",
    (
        ProcessPhase.STARTING,
        ProcessPhase.READY,
        ProcessPhase.RUNNING,
        ProcessPhase.STOPPING,
    ),
)
@local_test
def test_crash(crash_phase: ProcessPhase) -> None:
    """
    Tests that we can run multiple processes where one of them crashes.
    """
    manager = ProcessManager(
        processes=(
            ProcessInfo(
                module=__name__,
                name="proc1",
                args=(
                    "--manager-name",
                    "test_manager",
                    "--shutdown",
                    "CRASH",
                    "--last-phase",
                    crash_phase.name,
                ),
            ),
            ProcessInfo(
                module=__name__,
                name="proc2",
                args=("--manager-name", "test_manager", "--shutdown", "NORMAL"),
            ),
        ),
        name="test_manager",
        startup_period=TEST_STARTUP_PERIOD,
        shutdown_period=TEST_SHUTDOWN_PERIOD,
    )

    with pytest.raises(ProcessManagerException) as ex:
        manager.run()
    assert ex.value.failures == {"proc1": ProcessFailureType.CRASH, "proc2": None}


@pytest.mark.parametrize(
    "exception_phase",
    (
        ProcessPhase.STARTING,
        ProcessPhase.READY,
        ProcessPhase.RUNNING,
        ProcessPhase.STOPPING,
    ),
)
@local_test
def test_exception(exception_phase: ProcessPhase) -> None:
    """
    Tests that we can run multiple processes where one of them raises an exception.
    """
    manager = ProcessManager(
        processes=(
            ProcessInfo(
                module=__name__,
                name="proc1",
                args=(
                    "--manager-name",
                    "test_manager",
                    "--shutdown",
                    "EXCEPTION",
                    "--last-phase",
                    exception_phase.name,
                ),
            ),
            ProcessInfo(
                module=__name__,
                name="proc2",
                args=("--manager-name", "test_manager", "--shutdown", "NORMAL"),
            ),
        ),
        name="test_manager",
        startup_period=TEST_STARTUP_PERIOD,
        shutdown_period=TEST_SHUTDOWN_PERIOD,
    )

    with pytest.raises(ProcessManagerException) as ex:
        manager.run()
    assert ex.value.failures == {"proc1": ProcessFailureType.EXCEPTION, "proc2": None}


@pytest.mark.parametrize(
    "hang_phase",
    (
        ProcessPhase.STARTING,
        ProcessPhase.READY,
        ProcessPhase.RUNNING,
        ProcessPhase.STOPPING,
    ),
)
@local_test
def test_hang(hang_phase: ProcessPhase) -> None:
    """
    Tests that we can run multiple processes where one of them hangs.
    """
    manager = ProcessManager(
        processes=(
            ProcessInfo(
                module=__name__,
                name="proc1",
                args=(
                    "--manager-name",
                    "test_manager",
                    "--shutdown",
                    "HANG",
                    "--last-phase",
                    hang_phase.name,
                ),
            ),
            ProcessInfo(
                module=__name__,
                name="proc2",
                args=("--manager-name", "test_manager", "--shutdown", "NORMAL"),
            ),
        ),
        name="test_manager",
        startup_period=TEST_STARTUP_PERIOD,
        shutdown_period=TEST_SHUTDOWN_PERIOD,
    )

    with pytest.raises(ProcessManagerException) as ex:
        manager.run()
    assert ex.value.failures == {"proc1": ProcessFailureType.HANG, "proc2": None}


@click.command()
@click.option(f"--{ProcessManagerState.SUBPROCESS_ARG}", required=True)
@click.option("--process-name", required=True)
@click.option("--manager-name", required=True)
@click.option("--shutdown", required=True)
@click.option("--last-phase")
def child_main(
    process_manager_state_file: str,
    process_name: str,
    manager_name: str,
    shutdown: str,
    last_phase: Optional[str] = None,
) -> None:
    proc(
        ProcessManagerState.load(process_manager_state_file),
        process_name,
        manager_name,
        ShutdownBehavior[shutdown],
        ProcessPhase[last_phase] if last_phase is not None else ProcessPhase.TERMINATED,
    )


if __name__ == "__main__":
    if f"--{ProcessManagerState.SUBPROCESS_ARG}" in sys.argv:
        child_main()
