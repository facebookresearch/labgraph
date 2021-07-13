#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import os
from pathlib import Path

import appdirs
import yappi

from ..graphs.module import Module
from ..util.logger import get_logger


logger = get_logger(__name__)


def should_profile() -> bool:
    return "PROFILE" in os.environ


def write_profiling_results(module: Module) -> None:
    """
    Writes profiling results for the `LocalRunner` session to disk. The .pstat file
    can be read with the Python pstat module.
    """
    results_dir = appdirs.user_log_dir("labgraph", "labgraph")
    results_path = Path(results_dir) / Path(
        f"profile_{module.__class__.__name__}_{module.id}.pstat"
    )
    results_path.parent.mkdir(parents=True, exist_ok=True)
    yappi.get_func_stats().save(str(results_path), type="pstat")
    logger.info(f"{module}:saved profiling results to {results_path}")
