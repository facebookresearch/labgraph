#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import re
import os
from pathlib import Path
from typing import List, Tuple

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

def parse_sources(input: List[str]) -> List[str | int]:
    """
    Parse a list of string sources into ints or full paths to files or directories
    """
    sources = []
    for arg in input:
        if arg.isdigit():
            sources.append(int(arg))
        else:
            sources.append(absolute_path(arg))
    return sources

def parse_resolutions(num_sources: int, resolutions: List[str], default_resolution: Tuple[int, int, int] = (1280, 720, 30)) -> List[Tuple[int, int, int]]:
    """
    Convert a list of strings in format 'id:WxHxFPS' to a list of tuples

    Output will match `num_sources` in length. `default_resolution` will be placed where there is none provided in `resolutions` for that index

    `default_resolution` will be overridden by any entry with `*` as its id
    """
    default_res = None
    output = [None] * num_sources
    for i in range(len(resolutions)):
        colon_split = resolutions[i].split(":")
        x_split = colon_split[1].split("x")
        stream_id = -1 if colon_split[0] == "*" else int(colon_split[0])
        resolution = (int(x_split[0]), int(x_split[1]), int(x_split[2]))
        if stream_id > -1:
            output[stream_id] = resolution
        else:
            default_res = resolution
    
    if default_res is None:
        default_res = default_resolution
    for i in range(len(output)):
        if output[i] is None:
            output[i] = default_res
    
    return output