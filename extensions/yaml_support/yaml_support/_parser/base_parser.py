#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABCMeta, abstractmethod
from typing import List, Any


class BaseParser(metaclass=ABCMeta):
    """
    An abstraction for parsers
    """

    @abstractmethod
    def parse(self, code: str) -> List[Any]:
        raise NotImplementedError()
