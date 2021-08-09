#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from enum import Enum
from typing import Tuple, Union


# This is the default timer interval which determines the refresh rate of plots
# Unit is ms (~30fps)
# You can override this to change the refresh rate
TIMER_INTERVAL = 33


class Command(str, Enum):
    NONE = "none"
    CLEAR = "clear"


class AutoRange:
    pass


AxisRange = Union[AutoRange, Tuple[float, float]]
