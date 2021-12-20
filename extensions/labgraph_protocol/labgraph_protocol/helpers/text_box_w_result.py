#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import typing

from labgraph_protocol.helpers.common import (
    get_position,
    get_absolute_position,
    POSITION_T,
    RANDOM,
)
from labgraph_protocol.helpers.label_widget import get_label_widget
from labgraph_protocol.qt_stimulus import Deferred, QtStimulus
from labgraph_protocol.stimulus import Stimulus, BEGINNING, INFINITE


def get_text_box_w_result(
    instruction: str,
    result_key: str,
    start_at: float = BEGINNING,
    duration: float = INFINITE,
    position: POSITION_T = RANDOM,
) -> typing.List[Stimulus]:
    position = get_position(position, (0, 0))
    label = get_label_widget(duration=duration, text=instruction, position=position)
    textbox = QtStimulus(
        start_at=start_at,
        duration=duration,
        qt_type="QLineEdit",
        callbacks=[
            (
                "move",
                Deferred(
                    get_absolute_position,
                    # Can't use label directly because ser/des creates a new one
                    [Deferred("trial.stimuli.__getitem__", 0), (0, -20)],
                    unpack=True,
                ),
            ),
            (
                "returnPressed.connect",
                Deferred(
                    "add_trial_result_callback",
                    [
                        result_key,
                        Deferred("widget.text"),
                    ],
                ),
            ),
            ("returnPressed.connect", Deferred("trial.end")),
        ],
    )
    return [label, textbox]
