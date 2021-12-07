#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABCMeta, abstractstaticmethod


class BaseLoader(metaclass=ABCMeta):
    """
    An abstraction for file loaders
    """
    @abstractstaticmethod
    def load_from_file() -> str:
        pass
