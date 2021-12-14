#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from labgraph_protocol.helpers.audio_player import get_audio_player
from labgraph_protocol.protocol import (
    Condition,
    GET_TRIALS_T,
    Trial,
)
from labgraph_protocol.stimulus import Stimulus

PKG = "labgraph_protocol.examples"


class AudioCondition(Condition):
    PLAY_AUDIO = "PLAY_AUDIO"


def _get_stimulus() -> Stimulus:
    return get_audio_player(duration=8.0, pkg=PKG, filename="audio_player.mp3")


def get_trials() -> GET_TRIALS_T:
    yield [
        Trial(AudioCondition.PLAY_AUDIO, [_get_stimulus()]),
    ]
