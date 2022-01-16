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
    version="2.0.0",
    description="Research-friendly framework for in-lab experiments",
    long_description="LabGraph is a Python framework for rapidly prototyping experimental " +
                "systems for real-time streaming applications. " +
                "It is particularly well-suited to real-time neuroscience, " +
                "physiology and psychology experiments.",
    url="https://github.com/facebookresearch/labgraph",
    license="MIT",
    keywords="python streaming framework, reality lab, neuroscience, physiology, psychology",
    packages=find_packages(),
    package_data={"labgraph": ["tests/mypy.ini"]},
    python_requires=">=3.6",
    ext_modules=LIBRARY_EXTENSIONS,
    cmdclass={"build_ext": buck_build_ext},
    install_requires=[
        "appdirs==1.4.4",
        "click==8.0.3",
        "mypy==0.931",
        "pyzmq==22.3.0",
        "yappi==1.3.3",
        "psutil==5.9.0",
        "pytest-mock==3.6.1",
        "pytest==6.2.5",
        "pylsl==1.15.0",
        "typeguard==2.13.3",
        "typing-compat==0.1.0;python_version<'3.8'",
        "h5py==2.10.0;python_version<'3.8'",
        "h5py==3.6.0;python_version>='3.8'",
        "dataclasses==0.8;python_version=='3.6'",
        "numpy==1.19.5;python_version=='3.6'",
        "numpy==1.21.5;python_version=='3.7'",
        "numpy==1.22.1;python_version>='3.8'",
        "websockets==9.1;python_version=='3.6'",
        "websockets==10.1;python_version>='3.7'",
        "matplotlib==3.3.4;python_version=='3.6'",
        "matplotlib==3.5.1;python_version>='3.7'",
    ],
)

