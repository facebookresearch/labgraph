#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from labgraph_protocol.helpers.image_widget import get_image_widget
from labgraph_protocol.protocol import (
    Condition,
    GET_TRIALS_T,
    Trial,
)
from labgraph_protocol.stimulus import Stimulus

PKG = "labgraph_protocol.examples"


class ImageCondition(Condition):
    SHOW_IMAGE = "SHOW_IMAGE"


def _get_stimulus() -> Stimulus:
    return get_image_widget(
        duration=4.0, width=320, height=240, pkg=PKG, filename="display_image.jpg"
    )


def get_trials() -> GET_TRIALS_T:
    yield [
        Trial(ImageCondition.SHOW_IMAGE, [_get_stimulus()]),
    ]
