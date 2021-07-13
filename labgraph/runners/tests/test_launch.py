#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import sys
import tempfile

from ...util.random import random_string
from ..launch import launch


def test_launch() -> None:
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.close()
    string = random_string(10)

    launch(__name__, [temp_file.name, string]).wait()
    with open(temp_file.name, "r") as output_file:
        result = output_file.read()
    assert result == string


if __name__ == "__main__":
    filename = sys.argv[1]
    string = sys.argv[2]
    with open(filename, "w") as output_file:
        output_file.write(string)
