#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from buck_ext import BuckExtension, buck_build_ext
from setuptools import find_packages, setup

LIBRARY_EXTENSIONS = [
    BuckExtension(
        name="cthulhubindings",
        target="//:cthulhubindings#default,shared",
    ),
    BuckExtension(
        name="labgraph_cpp",
        target="//:labgraph_cpp_bindings#default,shared",
    ),
    BuckExtension(
        name="MyCPPNodes",
        target="//:MyCPPNodes#default,shared",
    ),
]


setup(
    name="labgraph",
    version="1.0.0",
    description="Python streaming framework",
    packages=find_packages(),
    package_data={"labgraph": ["tests/mypy.ini"]},
    python_requires=">=3.6, <3.7",
    ext_modules=LIBRARY_EXTENSIONS,
    cmdclass={"build_ext": buck_build_ext},
    install_requires=[
        "appdirs==1.4.3",
        "click==7.0",
        "dataclasses==0.6",
        "h5py==2.10.0",
        "matplotlib==3.1.1",
        "mypy==0.782",
        "numpy==1.16.4",
        "psutil==5.6.7",
        "pytest==3.10.1",
        "pytest_mock==2.0.0",
        "pyzmq==18.1.0",
        "typeguard==2.5.1",
        "typing_extensions==3.7.4",
        "yappi==1.2.5",
    ],
)
