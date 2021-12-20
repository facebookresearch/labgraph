#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import enum
import typing
from dataclasses import dataclass, field

import labgraph as lg
from labgraph_protocol.stimulus import Stimulus

RESULTS_T = typing.Dict[str, typing.Any]
TRIAL_RESULTS_T = typing.Dict[int, RESULTS_T]


class Condition(str, enum.Enum):
    pass


class BaseCondition(Condition):
    EXPERIMENT_START = "EXPERIMENT_START"


@dataclass
class ExperimentState:
    trial_results: TRIAL_RESULTS_T = field(default_factory=dict)


@dataclass
class Trial:
    condition: Condition
    stimuli: typing.List[Stimulus]
    results: RESULTS_T = field(default_factory=dict, compare=False)
    identifier: typing.Optional[int] = field(default=None, compare=False)

    def __post_init__(self) -> None:
        for stimulus in self.stimuli:
            stimulus.trial = self
        if self.identifier is None:
            self.identifier = id(self)

    def end(self) -> None:
        for stimulus in self.stimuli:
            stimulus.end()


class ReadyMessage(lg.Message):
    ready: bool


GET_TRIALS_T = typing.Generator[typing.List[Trial], ExperimentState, None]
