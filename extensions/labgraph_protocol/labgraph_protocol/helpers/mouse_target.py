#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import random
import typing

from labgraph_protocol.helpers.common import (
    get_position,
    POSITION_T,
    RANDOM,
)
from labgraph_protocol.qt_stimulus import Deferred, QtStimulus
from labgraph_protocol.stimulus import Stimulus, BEGINNING, INFINITE
from PyQt5 import QtCore, QtGui


def get_mouse_target(
    duration: float = INFINITE,
    position: POSITION_T = RANDOM,
    width: int = 50,
    height: int = 50,
    brush: QtGui.QColor = QtCore.Qt.cyan,
    pen: QtGui.QColor = QtCore.Qt.transparent,
    start_at: float = BEGINNING,
    hover_time: float = 0.0,
) -> typing.List[Stimulus]:
    position = get_position(position, (width, height))
    return QtStimulus(
        start_at=start_at,
        duration=duration,
        qt_type="QGraphicsRectItemWithHover",
        callbacks=[
            ("setRect", (position, width, height)),
            ("setBrush", brush),
            ("setPen", pen),
            ("setHoverEnterCallAt", hover_time),
            ("setHoverEnterCallback", Deferred("create_end_timer")),
            ("setHoverLeaveCallback", Deferred("cancel_end_timer")),
        ],
    )
