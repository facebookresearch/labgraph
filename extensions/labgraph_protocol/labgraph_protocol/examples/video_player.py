#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from labgraph_protocol.helpers.video_player import get_video_player
from labgraph_protocol.protocol import (
    Condition,
    GET_TRIALS_T,
    Trial,
)
from labgraph_protocol.stimulus import Stimulus

PKG = "labgraph_protocol.examples"


class VideoCondition(Condition):
    PLAY_VIDEO = "PLAY_VIDEO"


def _get_stimulus() -> Stimulus:
    return get_video_player(duration=9.0, pkg=PKG, filename="video_player.mp4")


def get_trials() -> GET_TRIALS_T:
    yield [
        Trial(VideoCondition.PLAY_VIDEO, [_get_stimulus()]),
    ]
