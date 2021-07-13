#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time

import pytest

from ...util.testing import local_test
from ..clock import ClockController, ExperimentClock


NUM_BUSY_TICKS = 100
NUM_TICKS = 10
CLOCK_READ_DELAY = 0.1
ACCEPTABLE_DELTA = 0.02
CLOCK_WAIT = 1


@local_test
def test_manual_busy_tick() -> None:
    """
    Tests that we can continuously tick forward the clock
    without delay using the controller and have the correct time
    read back by a regular experiment clock.
    """

    controllable_clock: ClockController = ClockController()
    local_clock: ExperimentClock = ExperimentClock()

    controllable_clock.set_time(0.0)
    for i in range(1, NUM_BUSY_TICKS + 1):
        controllable_clock.tick(1)
        read_time = local_clock.get_time()
        assert read_time == i


@local_test
def test_regular_clock_time() -> None:
    """
    Tests that we can query back regular system time through
    the clock as default behaviour.
    """

    controllable_clock: ClockController = ClockController()
    system_time = time.time()
    local_clock: ExperimentClock = ExperimentClock()

    controllable_clock.start(system_time)
    for _ in range(NUM_TICKS):
        read_time = local_clock.get_time()
        system_time = time.time()
        assert system_time - read_time < ACCEPTABLE_DELTA
        time.sleep(CLOCK_READ_DELAY)


@local_test
def test_clock_with_realtime_factor() -> None:
    """
    Tests that we can successfully set and use a realtime
    factor on the clock.
    """

    controllable_clock: ClockController = ClockController()
    local_clock: ExperimentClock = ExperimentClock()
    test_factor: float = 5.0

    assert controllable_clock.is_paused()
    controllable_clock.set_realtime_factor(test_factor)
    assert controllable_clock.is_paused()  # Should still be paused

    start_time = time.time()
    controllable_clock.start(start_time)

    time.sleep(CLOCK_WAIT)  # Wait for some time to elapse
    system_time = time.time()
    experiment_time = local_clock.get_time()

    system_time_diff = system_time - start_time
    experiment_time_diff = experiment_time - start_time

    assert experiment_time_diff >= (system_time_diff * test_factor - ACCEPTABLE_DELTA)
    assert experiment_time_diff <= (system_time_diff * test_factor + ACCEPTABLE_DELTA)
