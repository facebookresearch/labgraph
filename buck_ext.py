#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import os
import platform
import shutil
import subprocess

from setuptools import Extension
from setuptools.command.build_ext import build_ext


CONFIG_FILE = {
    "Windows": "win.buckconfig",
}.get(platform.system(), "unix.buckconfig")


class BuckExtension(Extension):
    def __init__(self, name: str, target: str) -> None:
        # don't invoke the original build_ext
        super().__init__(name, sources=[])
        self.target = target


class buck_build_ext(build_ext):
    def build_extensions(self) -> None:
        if "DF_SKIP_BUCK_BUILD" in os.environ:
            return
        assert shutil.which("buck") is not None, (
            "Could not find buck on the PATH\n"
            "To install Buck please see https://buck.build/setup/getting_started.html"
        )
        exts_by_target = {
            ext.target: ext for ext in self.extensions if isinstance(ext, BuckExtension)
        }
        result = (
            subprocess.check_output(
                ["buck", "build", "--show-output", "--config-file", CONFIG_FILE]
                + list(exts_by_target.keys())
            )
            .decode("utf-8")
            .strip()
        )
        for line in result.split("\n"):
            target, output_path = line.split(" ")
            shutil.copy(output_path, self.get_ext_fullpath(exts_by_target[target].name))
