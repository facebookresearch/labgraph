#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import abc
import threading
import typing
from dataclasses import dataclass

BEGINNING = 0.0
INFINITE = float("inf")


@dataclass
class Stimulus(abc.ABC):
    start_at: float
    duration: float
    # TODO: Provide a way to end whole trial immediately based on experiment state

    def __post_init__(self) -> None:
        self._start_at_timer = None
        self._duration_timer = None
        self._end_timer = None
        self._completed = False

    def setup(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        pass

    @abc.abstractmethod
    def enable(self) -> None:
        """
        Sublcasses should specify what enabling a stimulus entails
        """

    @abc.abstractmethod
    def disable(self) -> None:
        """
        Sublcasses should specify what disabling a stimulus entails
        """

    def teardown(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        pass

    @property
    def completed(self) -> bool:
        return self._completed

    def _start_at_callback(self) -> None:
        self.enable()
        if self.duration != INFINITE:
            self._duration_timer = threading.Timer(self.duration, self.end)
            self._duration_timer.start()

    def start(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.setup(*args, **kwargs)
        self._start_at_timer = threading.Timer(self.start_at, self._start_at_callback)
        self._start_at_timer.start()

    def create_end_timer(self, call_at: float) -> None:
        self.cancel_end_timer(call_at)
        self._end_timer = threading.Timer(call_at, self.end)
        self._end_timer.start()

    def cancel_end_timer(self, call_at: float) -> None:
        if self._end_timer is not None:
            self._end_timer.cancel()

    def end(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        if self._start_at_timer is not None:
            self._start_at_timer.cancel()
            self._start_at_timer = None
        if self._duration_timer is not None:
            self._duration_timer.cancel()
            self._duration_timer = None
        if self._end_timer is not None:
            self._end_timer.cancel()
            self._end_timer = None
        self.disable()
        self.teardown(*args, **kwargs)
        self._completed = True

    def add_trial_result(self, name: str, result: typing.Any) -> None:
        if callable(result):
            value = result()
        else:
            value = result
        # Note: self.trial is set by the containing trial object
        self.trial.results[name] = value

    def add_trial_result_callback(
        self, name: str, result: typing.Any
    ) -> typing.Callable[..., typing.Any]:
        def wrapper() -> None:
            self.add_trial_result(name, result)

        return wrapper
