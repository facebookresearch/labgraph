#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

class PythonFileLoaderError(Exception):
    """
    Represents a PythonFileLoader error.
    `PythonFileLoaderError` will be raised when an error is tied
    to .py file loading
    """
    pass


class YamlFileLoaderError(Exception):
    """
    Represents a YamlFileLoader error.
    `YamlFileLoaderError` will be raised when an error is tied
    to .yaml file loading
    """
    pass
