#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import typing

from labgraph_protocol.helpers.common import get_filepath
from labgraph_protocol.qt_stimulus import Deferred, QtStimulus
from labgraph_protocol.stimulus import Stimulus, BEGINNING


def get_audio_player(
    duration: float,
    filename: str,
    pkg: typing.Optional[str] = None,
    start_at: float = BEGINNING,
) -> Stimulus:
    return QtStimulus(
        start_at=start_at,
        duration=duration,
        qt_type="QMediaPlayerWithMediaContent",
        callbacks=[
            (
                "setMedia",
                Deferred("player.getMediaContent", get_filepath(filename, pkg)),
            ),
        ],
    )
