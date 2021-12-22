#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from labgraph_protocol.helpers.label_widget import get_label_widget
from labgraph_protocol.helpers.mouse_target import get_mouse_target
from labgraph_protocol.protocol import (
    Condition,
    GET_TRIALS_T,
    Trial,
)
from labgraph_protocol.stimulus import Stimulus


class TargetCondition(Condition):
    LABEL = "LABEL"
    TARGET = "TARGET"


def _get_stimulus() -> Stimulus:
    return get_label_widget(duration=1.5, text="Experiment start", position=(240, 240))


def _get_target() -> Stimulus:
    return get_mouse_target(hover_time=1.0)


def get_trials() -> GET_TRIALS_T:
    yield [Trial(TargetCondition.LABEL, [_get_stimulus()])]
    for _ in range(4):
        yield [Trial(TargetCondition.TARGET, [_get_target()])]
