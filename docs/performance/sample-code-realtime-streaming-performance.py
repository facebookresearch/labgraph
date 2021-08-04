#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import getpass
import logging
import tempfile

from datetime import timedelta
from io import BytesIO
from pathlib import Path

import h5py

RECORDING_FILENAMES = {
    ("linux", "c++"): "load_test_cpp_linux.h5",
    ("linux", "python"): "load_test_python.h5",
    ("mac", "c++"): "load_test_cpp_mac.h5",
    ("mac", "python"): "load_test_python_mac.h5",
    ("win", "c++"): "load_test_cpp_win.h5",
    ("win", "python"): "load_test_python_win.h5",
}
DATASETS = ("sample_summary", "count")
