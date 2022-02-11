#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import sys
import typing

try:
    typing.get_origin
except AttributeError as e:
    import typing_compat
    typing.get_origin = typing_compat.get_origin

# type_ is an instance of typing._GenericAlias
# generic is an instance of typing.Generic
def is_generic_subclass(type_: typing.Any, generic: typing.Any) -> bool:
        return typing.get_origin(type_) is generic  # type: ignore

