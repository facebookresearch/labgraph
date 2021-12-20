#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import typing

from labgraph_protocol.helpers.common import (
    get_position,
    POSITION_T,
    RANDOM,
)
from labgraph_protocol.qt_stimulus import CALLBACKS_T, QtStimulus
from labgraph_protocol.stimulus import Stimulus, BEGINNING


def get_label_widget(
    duration: float,
    text: str,
    start_at: float = BEGINNING,
    position: POSITION_T = RANDOM,
    additional_callbacks: typing.Optional[CALLBACKS_T] = None,
) -> Stimulus:
    position = get_position(position, (0, 0))
    if additional_callbacks is None:
        additional_callbacks = []
    callbacks = [
        ("setText", text),
        ("adjustSize", []),
        ("move", position),
    ]
    callbacks.extend(additional_callbacks)
    return QtStimulus(
        start_at=start_at,
        duration=duration,
        qt_type="QLabel",
        callbacks=callbacks,
    )
