#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import logging
import os


def get_log_level() -> str:
    return os.environ.get("LOGLEVEL", "INFO").upper()


logging.basicConfig(level=getattr(logging, get_log_level()))


def get_logger(module_name: str) -> logging.Logger:
    logger = logging.getLogger(module_name)
    logger.setLevel(get_log_level())
    return logger
