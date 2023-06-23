#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import time

class PerfUtility():
    """
    Utility class to measure function execution time

    Attributes:
        `delta_time`: `float` time in seconds between `update_start()` and `update_end()`
        `last_update_start`: `float` time in seconds when `update_start()` was last called
        `update_timer`: `float` time between `update_end()` calls, if >= 1 second, resets to 0
        `update_count`: `int` number of times `update_end()` is called, reset to 0 with `update_timer`
        `updates_per_second`: `int` the value of the last `update_count` before reset
        `averaged`: `bool` whether `update_timer` has reached >= 1 second for the first time
    
    Functions:
        `update_start(self) -> None`

        `update_end(self) -> None`

        `get_remaining_sleep_time(self, target_update_rate: int) -> float`
    """

    delta_time: float = 0.0
    last_update_start: float = 0.0
    update_timer: float = 0.0
    update_count: int = 0
    updates_per_second: int = 0
    averaged: bool = False

    def update_start(self) -> None:
        """
        Begin profiling function time

        Sets `last_update_start` to the current time
        """
        self.last_update_start = time.perf_counter()
    
    def update_end(self) -> None:
        """
        End profiling function time

        Sets `delta_time`, `updates_per_second`
        """
        self.delta_time = time.perf_counter() - self.last_update_start
        self.update_timer += self.delta_time
        self.update_count += 1
        if not self.averaged:
            self.updates_per_second = self.update_count

        if self.update_timer >= 1.0:
            self.updates_per_second = self.update_count
            self.update_timer = 0
            self.update_count = 0
            self.averaged = True
    
    def get_remaining_sleep_time(self, target_update_rate: int) -> float:
        """
        Get wait time in seconds for functions repeating at set intervals
        Takes `delta_time` into account
        """
        target_delta_time = 1.0 / target_update_rate
        actual_delta_time = time.perf_counter() - self.last_update_start
        sleep_time = target_delta_time - actual_delta_time
        return 0 if sleep_time < 0 else sleep_time