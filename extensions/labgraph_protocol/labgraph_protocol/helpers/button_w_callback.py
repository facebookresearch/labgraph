#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import typing

from labgraph_protocol.helpers.common import (
    get_position,
    POSITION_T,
    RANDOM,
)
from labgraph_protocol.qt_stimulus import Deferred, QtStimulus
from labgraph_protocol.stimulus import Stimulus, BEGINNING, INFINITE


def NOOP() -> None:
    pass


def get_button_w_callback(
    text: str,
    start_at: float = BEGINNING,
    duration: float = INFINITE,
    position: POSITION_T = RANDOM,
    callback: typing.Callable[..., typing.Any] = NOOP,
) -> Stimulus:
    position = get_position(position, (0, 0))
    return QtStimulus(
        start_at=start_at,
        duration=duration,
        qt_type="QPushButton",
        callbacks=[
            ("setText", text),
            ("clicked.connect", callback),
            ("clicked.connect", Deferred("end")),
            ("move", position),
        ],
    )
