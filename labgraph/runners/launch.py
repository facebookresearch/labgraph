#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import os
import platform
import shlex
import subprocess
import sys
from typing import Optional, Sequence

from ..util.logger import get_logger
from ..util.resource import get_resource_tempfile


logger = get_logger(__name__)


def launch(
    module: str, args: Optional[Sequence[str]] = None, *posargs, **kwargs
) -> subprocess.Popen:  # type: ignore
    """
    Runs the given module with the given arguments in a subprocess. This method for
    launching a subprocess works even when inside a PEX environment.

    Args:
        module: The module to run as the entry point.
        args: The arguments to pass to the child process.
        *args: Positional arguments forwarded to subprocess.Popen.
        **kwargs: Keyword arguments forwarded to subprocess.Popen.
    """
    args = args or []
    python_path = sys.executable
    if _in_pex():
        pex_env_path = _get_pex_path()
        parent_module = __name__.rsplit(".", 1)[0]
        pex_bin_path = get_resource_tempfile(parent_module, "pex")
        command = (
            f"{python_path} {pex_bin_path} --pex-path {pex_env_path} -m {module} -- "
            f"{_join_args(args)}"
        )
        env = os.environ.copy()
    else:
        command = f"{python_path} -m {module} {_join_args(args)}"
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}

    logger.debug(f"Launching subprocess: {command}")
    if platform.system() == "Windows":
        return subprocess.Popen(command, env=env, *posargs, **kwargs)  # type: ignore
    else:
        return subprocess.Popen(  # type: ignore
            shlex.split(command), env=env, *posargs, **kwargs
        )


def _join_args(args: Sequence[str]) -> str:
    if platform.system() == "Windows":
        return " ".join(args)
    else:
        return " ".join(shlex.quote(arg) for arg in args)


def _in_pex() -> bool:
    # HACK: There is currently no canonical way to detect whether we are running from
    # inside a PEX environment. This is a hack based on the fact that PEX adds a _pex
    # module inside the environment.
    # More information: https://github.com/pantsbuild/pex/issues/721
    try:
        import _pex  # type: ignore

        return True
    except ModuleNotFoundError:
        return False


def _get_pex_path() -> str:
    pex_path = sys.argv[0]
    if not pex_path.endswith(".pex"):
        raise RuntimeError(f"Could not find PEX path, found argv[0] = {pex_path}")
    return pex_path
