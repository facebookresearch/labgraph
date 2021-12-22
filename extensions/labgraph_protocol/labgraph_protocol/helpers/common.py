#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import random
import typing

import pkg_resources
from labgraph_protocol.qt_stimulus import Deferred, QtStimulus


class _Random:
    pass


COORDINATES_T = typing.Tuple[int, int]
POSITION_T = typing.Union[_Random, COORDINATES_T, Deferred]
RANDOM = _Random()


def get_random_position(
    window_size: COORDINATES_T, position: POSITION_T, element_size: COORDINATES_T
) -> COORDINATES_T:
    return (
        random.random() * (window_size[0] - element_size[0]),
        random.random() * (window_size[1] - element_size[1]),
    )


def get_absolute_position(
    anchor: QtStimulus, relative_position: COORDINATES_T
) -> COORDINATES_T:
    return (
        anchor.widget.x() - relative_position[0],
        anchor.widget.y() - relative_position[1],
    )


def get_position(position: POSITION_T, element_size: COORDINATES_T) -> POSITION_T:
    if position is RANDOM:
        return Deferred(
            get_random_position,
            [
                (
                    Deferred("parent.width", []),
                    Deferred("parent.height", []),
                ),
                position,
                element_size,
            ],
            unpack=True,
        )
    else:
        return position


def get_filepath(filename: str, pkg: typing.Optional[str] = None) -> str:
    if pkg is not None:
        return pkg_resources.resource_filename(pkg, filename)
    else:
        return filename
