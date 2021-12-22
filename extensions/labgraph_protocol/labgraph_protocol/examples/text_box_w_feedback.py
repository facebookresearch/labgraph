#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import typing

from labgraph_protocol.helpers.label_widget import get_label_widget
from labgraph_protocol.helpers.text_box_w_result import (
    get_text_box_w_result,
)
from labgraph_protocol.protocol import (
    Condition,
    ExperimentState,
    GET_TRIALS_T,
    Trial,
)
from labgraph_protocol.stimulus import Stimulus


class TextBoxCondition(Condition):
    TEXT_BOX = "TEXT_BOX"
    FEEDBACK = "FEEDBACK"


def _get_stimulus() -> typing.List[Stimulus]:
    return get_text_box_w_result(
        instruction="Enter 'hello' or any other string",
        duration=5.0,
        position=(0, 0),
        result_key="text_box",
    )


def _get_feedback_stimulus(
    experiment_state: ExperimentState, previous_trial_id: int
) -> Stimulus:
    previous_results = experiment_state.trial_results[previous_trial_id]
    if "text_box" not in previous_results:
        text = "MISS"
        color = "blue"
    elif previous_results["text_box"] == "hello":
        text = "RIGHT"
        color = "green"
    else:
        text = "WRONG"
        color = "red"
    return get_label_widget(
        duration=1.5,
        text=text,
        position=(0, 0),
        additional_callbacks=[("setStyleSheet", f"QLabel {{ color: {color} }}")],
    )


def get_trials() -> GET_TRIALS_T:
    for _ in range(3):
        text_box_trial = Trial(TextBoxCondition.TEXT_BOX, _get_stimulus())
        yield [text_box_trial]
        experiment_state = yield
        yield [
            Trial(
                TextBoxCondition.FEEDBACK,
                [_get_feedback_stimulus(experiment_state, text_box_trial.identifier)],
            ),
        ]
