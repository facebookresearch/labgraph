#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import re
import os
from pathlib import Path

def absolute_path(path: str) -> str:
    """
    Returns the absolute path to a file/directory from the current working directory if given a relative path
    Cleans trailing seperators, and ensures the directory exists
    """
    _path = path
    if not _path.startswith("/") or not re.match(r'[a-zA-Z]:', _path):
        _path = os.path.join(os.path.dirname(os.getcwd()), _path)
    Path(os.path.dirname(_path)).mkdir(parents = True, exist_ok = True)
    return _path

def relative_latency(cur_device_time: float, cur_receive_time: float, first_device_time: float, first_receive_time: float) -> float:
    """
    Calcuate relative latency value for current set of times
    """
    return (cur_receive_time - first_receive_time) - (cur_device_time - first_device_time)