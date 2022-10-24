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
    _path = _path.removesuffix("/").removesuffix("\\")
    Path(os.path.dirname(_path)).mkdir(parents = True, exist_ok = True)
    return _path