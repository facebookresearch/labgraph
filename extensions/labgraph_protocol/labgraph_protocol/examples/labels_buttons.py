#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from labgraph_protocol.helpers.button_w_callback import (
    get_button_w_callback,
)
from labgraph_protocol.helpers.label_widget import get_label_widget
from labgraph_protocol.protocol import (
    Condition,
    GET_TRIALS_T,
    Trial,
)
from labgraph_protocol.stimulus import Stimulus


class DummyCondition(Condition):
    DUMMY_TRIAL = "DUMMY_TRIAL"


def _get_stimulus() -> Stimulus:
    return get_label_widget(duration=1.5, text="DUMMY_LABEL_TEXT")


def _get_clicky_stimulus() -> Stimulus:
    return get_button_w_callback(text="DUMMY_BUTTON_TEXT")


def get_trials() -> GET_TRIALS_T:
    yield [
        Trial(DummyCondition.DUMMY_TRIAL, [_get_stimulus()]),
        Trial(DummyCondition.DUMMY_TRIAL, [_get_stimulus(), _get_clicky_stimulus()]),
        Trial(DummyCondition.DUMMY_TRIAL, [_get_stimulus()]),
        Trial(DummyCondition.DUMMY_TRIAL, [_get_clicky_stimulus()]),
    ]
