#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import time

class PerfUtility():
    """
    Utility class to measure function execution time

    Attributes:
        `NANOSECOND`: `int` constant, number of nanoseconds in one second
        `MILISECOND`: `int` constant, number of miliseconds in one second
        `delta_time_ns`: `int` time in nanoseconds between `update_start()` and `update_end()`
        `last_update_start_ns`: `int` time in nanoseconds when `update_start()` was last called
        `update_timer_ns`: `int` time between `update_end()` calls, if >= 1 second, resets to 0
        `update_count`: `int` number of times `update_end()` is called, reset to 0 with `update_timer_ns`
        `updates_per_second`: `int` the value of the last `update_count` before reset
        `averaged`: `bool` whether `update_timer_ns` has reached >= 1 second for the first time
    
    Functions:
        `update_start(self) -> None`

        `update_end(self) -> None`

        `get_sleep_time_ns(cls, start_time_ns: int, target_update_rate: int) -> int`

        `ns_to_s(cls, time_ns: int) -> float`

        `ns_to_ms(cls, time_ns: int) -> int`
    """
    NANOSECOND: int = 1^9
    MILISECOND: int = 1^6

    delta_time_ns: int = 0
    last_update_start_ns: int = 0
    update_timer_ns: int = 0
    update_count: int = 0
    updates_per_second: int = 0
    averaged: bool = False

    def update_start(self) -> None:
        """
        Begin profiling function time

        Sets `last_update_start_ns` to the current time
        """
        self.last_update_start_ns = time.time_ns()
    
    def update_end(self) -> None:
        """
        End profiling function time

        Sets `delta_time_ns`, `updates_per_second`
        """
        self.delta_time_ns = time.time_ns() - self.last_update_start_ns
        self.update_timer_ns += self.delta_time_ns
        self.update_count += 1
        if not self.averaged:
            self.updates_per_second = self.update_count

        if self.update_timer_ns >= PerfUtility.NANOSECOND:
            self.updates_per_second = self.update_count
            self.update_timer_ns = 0
            self.update_count = 0
            self.averaged = True
    
    @classmethod
    def get_sleep_time_ns(cls, start_time_ns: int, target_update_rate: int) -> int:
        """
        Get wait time in nanoseconds for functions repeating at set intervals
        Takes `delta_time_ns` into account
        """
        target_delta_time_ns = int(PerfUtility.NANOSECOND / target_update_rate)
        actual_delta_time_ns = time.time_ns() - start_time_ns
        sleep_time = target_delta_time_ns - actual_delta_time_ns
        return 0 if sleep_time < 0 else sleep_time
    
    @classmethod
    def ns_to_s(cls, time_ns: int) -> float:
        """
        Convert nanosecond to second
        """
        return time_ns / PerfUtility.NANOSECOND

    @classmethod
    def ns_to_ms(cls, time_ns: int) -> int:
        """
        Convert nanosecond to milisecond
        """
        return int(time_ns / PerfUtility.MILISECOND)