#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import time

class PerfUtility():    
    NANOSECOND: int = 1000000000
    MILISECOND: int = 1000000

    delta_time_ns: int = 0
    last_update_start_ns: int = 0
    update_timer_ns: int = 0
    update_count: int = 0
    updates_per_second: int = 0
    averaged: bool = False

    def update_start(self):
        self.last_update_start_ns = time.time_ns()
    
    def update_end(self):
        self.delta_time_ns = time.time_ns() - self.last_update_start_ns
        self.update_timer_ns += self.delta_time_ns
        self.update_count += 1
        if not self.averaged:
            self.updates_per_second = self.update_count

        if self.update_timer_ns >= 1000000000:
            self.updates_per_second = self.update_count
            self.update_timer_ns = 0
            self.update_count = 0
            self.averaged = True
    
    @classmethod
    def get_sleep_time_ns(cls, start_time_ns: int, target_update_rate: int) -> int:
        target_delta_time_ns = int(PerfUtility.NANOSECOND / target_update_rate)
        actual_delta_time_ns = time.time_ns() - start_time_ns
        sleep_time = target_delta_time_ns - actual_delta_time_ns
        return 0 if sleep_time < 0 else sleep_time
    
    @classmethod
    def ns_to_s(cls, time_ns: int) -> float:
        return time_ns / PerfUtility.NANOSECOND

    @classmethod
    def ns_to_ms(cls, time_ns: int) -> int:
        return int(time_ns / PerfUtility.MILISECOND)