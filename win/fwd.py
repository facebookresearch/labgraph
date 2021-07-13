#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import pathlib, sys, subprocess, shlex, shutil

executables = {
    "ar": "lib",
    "cxx": "cl",
    "cxxpp": "cl",
    "ld": "link",
}


def main() -> None:
    exec_type = sys.argv[1]
    assert exec_type in executables.keys(), f"Unknown executable type '{exec_type}'"

    executable = executables[exec_type]
    exec_path = shutil.which(executable)
    assert exec_path is not None, f"Could not find executable '{executable}' on PATH"
    assert pathlib.Path(
        exec_path
    ).is_file(), f"Executable does not exist at {exec_path}"

    args = [exec_path] + sys.argv[2:]

    proc = subprocess.Popen(args, stdout=sys.stdout, stderr=subprocess.STDOUT)
    return_code = proc.wait()
    sys.exit(return_code)


if __name__ == "__main__":
    main()
