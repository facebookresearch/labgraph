#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from dataclasses import dataclass

from ....util.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ApiStreamDesc:
    stream_id: str
    stream_name: str

    def __init__(self, stream_id, stream_name):
        self.stream_id = stream_id
        self.stream_name = stream_name
