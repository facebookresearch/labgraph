#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

# Inspired by ROS Rate feature and this is a modified version of script below.
# https://github.com/ros/ros_comm/blob/noetic-devel/clients/rospy/src/rospy/timer.py


# Built-in imports
import time
import asyncio


class Rate(object):
    """
    Convenience class for sleeping in a loop at a specified rate
    """
    
    def __init__(self, hz):
        """
        Constructor.
        @param hz: hz rate to determine sleeping
        @type  hz: float
        """
        # #1403
        self.last_time = time.time()
        self.elapsed = 0.0
        self.sleep_dur = 1.0/hz

    def _remaining(self, curr_time):
        """
        Calculate the time remaining for rate to sleep.
        @param curr_time: current time
        @type  curr_time: float
        @return: time remaining
        @rtype: float
        """
        # detect time jumping backwards
        if self.last_time > curr_time:
            self.last_time = curr_time

        # calculate remaining time
        self.elapsed = curr_time - self.last_time
        return self.sleep_dur - self.elapsed

    def remaining(self):
        """
        Return the time remaining for rate to sleep.
        @return: time remaining
        @rtype: float
        """
        curr_time = time.time()
        return self._remaining(curr_time)

    async def sleep(self):

        curr_time = time.time()
        timeRemaining = self._remaining(curr_time)

        if timeRemaining > 0.0:
            await asyncio.sleep(timeRemaining)
        else:
            await asyncio.sleep(0)

        self.last_time = self.last_time + self.sleep_dur

        if curr_time - self.last_time > self.sleep_dur * 2:
            print("Time jumping forward detected")
            self.last_time = curr_time  

