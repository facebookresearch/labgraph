#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from .bindings import (  # type: ignore
    Clock,
    ClockAuthority,
    clockManager,
    ControllableClock,
)


class ExperimentClock:
    """
    Wrapper for a Cthulhu Clock.  All nodes which need to keep
    track of time should create its own instance of this clock.
    """

    def __init__(self) -> None:
        self.clock: Clock = clockManager().clock()

    def get_time(self) -> float:
        return self.clock.getTime()  # type: ignore


class ClockController:
    """
    Wrapper for Cthulhu's ControllableClock.  The state node responsible
    for 'ticking' forward the clock in a simulation should be its
    sole owner.

    Must either call start() or tick forward the clock manually.
    """

    CONTEXT_NAME = "clock_owner"

    def __init__(self) -> None:
        ClockAuthority(True, self.CONTEXT_NAME)
        self.controllable_clock: ControllableClock = clockManager().controlClock(
            self.CONTEXT_NAME
        )
        self.clock: ExperimentClock = ExperimentClock()
        self.controllable_clock.pause()
        self._is_paused: bool = True

    def _pause(self) -> None:
        if not self._is_paused:
            self.controllable_clock.pause()
            self._is_paused = True

    def is_paused(self) -> bool:
        return self._is_paused

    def start(self, start_time: float) -> None:
        """
        Starts running the clock at the specified start_time.
        """

        self.controllable_clock.start(start_time)
        self._is_paused = False

    def set_time(self, time: float, start_running: bool = False) -> None:
        """
        Sets the current time on the clock.  The optional
        start_running parameters specifies if the clock should
        run after this function call.
        """

        self._pause()

        if start_running:
            self.start(time)
        else:
            self.controllable_clock.setTime(time)

    def set_realtime_factor(self, factor: float) -> None:
        """
        Sets the realtime factor for the clock.  The clock will
        maintain whichever state it was in (running/paused) prior
        to this function being called.
        """

        should_restart: bool = not self._is_paused
        self._pause()

        self.controllable_clock.setRealtimeFactor(factor)
        if should_restart:
            curr_time: float = self.clock.get_time()
            self.controllable_clock.start(curr_time)

    def tick(self, increment_by: float = 1) -> None:
        """
        Ticks forward the current time on the clock, pausing the
        clock if it is not paused already.
        """

        self._pause()
        curr_time: float = self.clock.get_time()
        self.controllable_clock.setTime(curr_time + increment_by)
