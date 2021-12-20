#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import typing

from labgraph_protocol.helpers.common import (
    get_filepath,
    get_position,
    POSITION_T,
    RANDOM,
)
from labgraph_protocol.qt_stimulus import QtStimulus
from labgraph_protocol.stimulus import Stimulus, BEGINNING


def get_image_widget(
    duration: float,
    width: int,
    height: int,
    filename: str,
    pkg: typing.Optional[str] = None,
    start_at: float = BEGINNING,
    position: POSITION_T = RANDOM,
) -> Stimulus:
    position = get_position(position, (width, height))
    return QtStimulus(
        start_at=start_at,
        duration=duration,
        qt_type="QLabelWithPictureFromFilename",
        callbacks=[
            ("move", position),
            ("resize", (width, height)),
            ("setPictureFromFilename", get_filepath(filename, pkg)),
        ],
    )
