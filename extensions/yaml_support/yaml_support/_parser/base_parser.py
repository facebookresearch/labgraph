#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABCMeta, abstractmethod
from typing import List
from extensions.yaml_support.yaml_support.model.base_model import BaseModel


class BaseParser(metaclass=ABCMeta):
    """
    An abstraction for parsers
    """

    @abstractmethod
    def parse(self, code: str) -> List[BaseModel]:
        raise NotImplementedError()
