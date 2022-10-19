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
    path = path
    if not path.startswith("/") or not re.match(r'[a-zA-Z]:', path):
        path = os.path.join(os.path.dirname(os.getcwd()), path)
    path = path.removesuffix("/").removesuffix("\\")
    Path(os.path.dirname(path)).mkdir(parents = True, exist_ok = True)
    return path