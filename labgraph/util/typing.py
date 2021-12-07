#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import sys
import typing


# TODO: Remove all 3.8 checks once 3.6 is dead.
def is_py38() -> bool:
    return sys.version_info > (3, 8)


# type_ is an instance of typing._GenericAlias
# generic is an instance of typing.Generic
def is_generic_subclass(type_: typing.Any, generic: typing.Any) -> bool:
    if is_py38():
        return typing.get_origin(type_) is generic  # type: ignore
    else:
        return issubclass(type_, generic)
