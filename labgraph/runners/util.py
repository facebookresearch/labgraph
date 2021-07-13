#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import importlib
import inspect
from typing import Type

from ..graphs.module import Module


def get_module_class(python_module: str, python_class: str) -> Type[Module]:
    mod = importlib.import_module(python_module)

    if hasattr(mod, python_class):
        cls = getattr(mod, python_class)
    else:
        # We are going to check if the module was merely renamed by checking
        # the `__name__` attribute of every class in the module.
        real_class_name = python_class

        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if inspect.isclass(attr):
                if attr.__name__ == real_class_name:
                    # We found the rename
                    python_class = attr_name
                    break
        else:
            raise NameError(
                f"Could not find LabGraph a class in module `{python_module}`` with "
                f"the following class.__name__: `{real_class_name}`. "
                f"If it refers to an anonymous class, consider moving it "
                f"to the module scope of {python_module}."
            )
        cls = getattr(mod, python_class)
    assert issubclass(
        cls, Module
    ), f"Expected a subclass of {Module.__name__}, got {cls.__name__}"
    if not issubclass(cls, Module):
        raise TypeError(f"Expected a subclass of {Module.__name__}, got {cls.__name__}")
    return cls  # type: ignore
