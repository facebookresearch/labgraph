#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import os
import runpy
import shutil
import subprocess
import tempfile
from glob import glob
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import labgraph as lg

from ..runners.launch import _get_pex_path, _in_pex, launch
from ..util.logger import get_logger
from ..util.resource import get_resource_tempfile


SOURCE_PATH = "labgraph"

logger = get_logger(__name__)


def test_typecheck() -> None:
    """
    Typechecks LabGraph using mypy. Assumes that the test is running from a PEX (if
    not, the test skips).
    """
    mypy_ini_path = get_resource_tempfile(__name__, "mypy.ini")
    mypy_args = ["--config-file", mypy_ini_path]

    zip_path: Optional[str] = None
    try:
        # If available, get the path to the typecheck_src.zip source archive
        zip_path = get_resource_tempfile(__name__, "typecheck_src.zip")
    except FileNotFoundError:
        pass  # Just let zip_path be None and handle this case below

    temp_dir: Optional[tempfile.TemporaryDirectory] = None
    if zip_path is None:
        # If the source archive is not available, typecheck the installed location
        # for LabGraph
        src_path = str(Path(lg.__file__).parent)
        mypy_args += glob(f"{src_path}/**/*.py", recursive=True)
    else:
        # If available, typecheck the typecheck_src.zip source archive
        temp_dir = tempfile.TemporaryDirectory()  # noqa: P201
        src_path = temp_dir.name
        # Extract the source files from the zip file
        src_file = ZipFile(zip_path)
        for file_path in src_file.namelist():
            if file_path.startswith(SOURCE_PATH) and file_path.endswith(".py"):
                src_file.extract(file_path, src_path)
                mypy_args.append(file_path)

    # Typecheck in a subprocess
    mypy_proc = launch("mypy", mypy_args, cwd=src_path, stdout=subprocess.PIPE)
    mypy_output: Optional[str] = None
    if mypy_proc.stdout is not None:
        mypy_output = mypy_proc.stdout.read().decode("utf-8")
    mypy_proc.wait()

    if temp_dir is not None:
        temp_dir.cleanup()

    if mypy_proc.returncode != 0:
        error_message = f"Typechecking failed (exit code {mypy_proc.returncode})"
        if mypy_output is not None:
            logger.error(mypy_output)
            error_message += f":\n\n{mypy_output}"
        raise RuntimeError(error_message)
