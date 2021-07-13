#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from enum import Enum, IntEnum

import pytest

from ...util import LabGraphError
from ..config import Config
from ..node import Node


class MyIntEnum(IntEnum):
    A = 0
    B = 1


class MyStrEnum(str, Enum):
    A = "0"
    B = "1"


class MyConfig(Config):
    int_field: int
    str_field: str
    bool_field: bool
    float_field: float
    int_enum_field: MyIntEnum
    str_enum_field: MyStrEnum


class MyNode(Node):
    config: MyConfig

    def setup(self) -> None:
        self.config


def test_config_from_args() -> None:
    """
    Test that we can build a config from command-line arguments.
    """
    test_args = [
        "--int-field",
        "5",
        "--str-field",
        "hello",
        "--float-field",
        "0.5",
        "--int-enum-field",
        "B",
        "--str-enum-field",
        "A",
        "--bool-field",
    ]
    expected_config = {
        "int_field": 5,
        "str_field": "hello",
        "float_field": 0.5,
        "int_enum_field": MyIntEnum.B,
        "str_enum_field": MyStrEnum.A,
        "bool_field": True,
    }
    config = MyConfig.fromargs(args=test_args)
    assert config.asdict() == expected_config


def test_node_config() -> None:
    """
    Test that we can provide config to a node.
    """
    node = MyNode()
    node.configure(
        MyConfig(
            int_field=5,
            str_field="hello",
            float_field=0.5,
            int_enum_field=MyIntEnum.B,
            str_enum_field=MyStrEnum.A,
            bool_field=True,
        )
    )
    node.setup()


def test_node_no_config() -> None:
    """
    Test that accessing config on an unconfigured node throws a descriptive exception.
    """
    node = MyNode()

    with pytest.raises(LabGraphError) as err:
        node.setup()

    assert (
        "Configuration not set. Call MyNode.configure() to set the configuration."
        in str(err.value)
    )
