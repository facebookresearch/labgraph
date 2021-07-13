#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import argparse
from enum import Enum
from typing import Any, List, Optional

from ..messages.message import Field, Message
from ..util.error import LabGraphError


class Config(Message):
    """
    Represents a configuration for a module. A configuration defines how a module will
    behave.
    """

    @classmethod
    def fromargs(cls, args: Optional[List[str]] = None) -> "Config":
        """
        Builds a Config object based on command-line arguments.

        Args:
            args: Command-line arguments to parse. If not provided, looks at `sys.argv`.
        """
        parser = argparse.ArgumentParser()
        for field_name, field in cls.__message_fields__.items():
            _add_field_to_argument_parser(parser, field_name, field)
        if args is not None:
            parse_result = parser.parse_args(args)
        else:
            parse_result = parser.parse_args()
        return cls(**{k: v for k, v in vars(parse_result).items() if v is not None})


def _add_field_to_argument_parser(
    parser: argparse.ArgumentParser, field_name: str, field: Field[Any]
) -> None:
    """
    Adds an argument to the parser corresponding to the provided field.

    Args:
        parser: The argument parser
        field_name: The name of the field
        field: The field
    """
    field_name_dashes = field_name.replace("_", "-")
    field_option = f"--{field_name_dashes}"
    python_type = field.data_type.python_type
    if python_type in (int, str, float):
        parser.add_argument(field_option, type=python_type, required=field.required)
    elif python_type is bool:
        parser.add_argument(field_option, action="store_true")
    elif issubclass(python_type, Enum):
        parser.add_argument(
            field_option,
            type=lambda item: python_type[item],  # type: ignore
            choices=list(python_type),
            required=field.required,
        )
    else:
        raise LabGraphError(
            "Invalid type for argument parsing for config field. "
            f"'{field_name}' has type '{python_type.__name__}'"
        )
