#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import importlib
import itertools
import logging
import time
import typing

import labgraph as lg
from labgraph_protocol.priority_queue import Empty, PriorityQueue
from labgraph_protocol.protocol import (
    BaseCondition,
    ExperimentState,
    GET_TRIALS_T,
    ReadyMessage,
    Trial,
)

LOGGER = logging.getLogger(__name__)
PUBLISH_LOOP_TIME = 0.001


class CurrentTrialMessage(lg.TimestampedMessage):
    trial: Trial


class EndTrialMessage(lg.TimestampedMessage):
    trial: Trial
    reason: str


class ProtocolNodeState(lg.State):
    get_trials: typing.Optional[GET_TRIALS_T] = None
    pq: typing.Optional[PriorityQueue] = None
    priority: typing.Optional[typing.Generator[float, None, None]] = None
    shutdown: bool = False
    ready: bool = False
    current_trial: typing.Optional[Trial] = None
    experiment_state: typing.Optional[ExperimentState] = None


class ProtocolNodeConfig(lg.Config):
    module: str


class ProtocolNode(lg.Node):
    config: ProtocolNodeConfig
    state: ProtocolNodeState

    CURRENT_TRIAL_TOPIC = lg.Topic(CurrentTrialMessage)
    END_TRIAL_TOPIC = lg.Topic(EndTrialMessage)
    READY_TOPIC = lg.Topic(ReadyMessage)

    def setup(self) -> None:
        module = importlib.import_module(self.config.module)
        tie_breaker = getattr(module, "priority_queue_tie_breaker", None)
        self.state.get_trials = module.get_trials()
        self.state.pq = PriorityQueue(tie_breaker)
        self.state.priority = itertools.count()
        self.state.current_trial = Trial(BaseCondition.EXPERIMENT_START, [])
        self.state.experiment_state = ExperimentState()

    def cleanup(self) -> None:
        self.state.shutdown = True

    @lg.publisher(CURRENT_TRIAL_TOPIC)
    async def current_trial(self) -> lg.AsyncPublisher:
        while not self.state.shutdown:
            if self.state.ready:
                try:
                    self.state.current_trial = self.state.pq.pop()
                except Empty:
                    self._update_priority_queue()
                    continue
                self.state.ready = False
                yield (
                    self.CURRENT_TRIAL_TOPIC,
                    CurrentTrialMessage(
                        trial=self.state.current_trial,
                        timestamp=time.time(),
                    ),
                )
            await asyncio.sleep(PUBLISH_LOOP_TIME)

    @lg.subscriber(READY_TOPIC)
    def ready(self, message: ReadyMessage) -> None:
        self.state.ready = message.ready

    @lg.subscriber(END_TRIAL_TOPIC)
    def end_trial(self, message: EndTrialMessage) -> None:
        if message.trial == self.state.current_trial:
            self.state.ready = True
            self.state.experiment_state.trial_results[
                message.trial.identifier
            ] = message.trial.results
        else:
            LOGGER.warn(
                f"Tried to end trial {message.trial} "
                f"with reason '{message.reason}' "
                f"but {self.state.current_trial} is currently active."
            )

    def _update_priority_queue(self) -> None:
        try:
            trials = self.state.get_trials.send(None)
            # If the generator has a send line, this will be True
            if trials is None:
                trials = self.state.get_trials.send(self.state.experiment_state)
        except StopIteration:
            raise lg.NormalTermination()
        priority = next(self.state.priority)
        for trial in trials:
            self.state.pq.push(trial, priority)
