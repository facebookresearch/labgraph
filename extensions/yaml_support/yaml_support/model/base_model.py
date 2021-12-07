#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABCMeta, abstractmethod


class BaseModel(metaclass=ABCMeta):
    """
    An abstraction for models.
    A model is a class that stores data related to a python object
    """
    @abstractmethod
    def save(self, path: str) -> None:
        """
        Saves the data stored by the model into a file
        Args:
            path: The path of the file where the model should be stored.
        """
        pass
