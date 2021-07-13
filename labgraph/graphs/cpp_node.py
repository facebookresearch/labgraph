#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from dataclasses import field
from typing import Any, List, Optional, Type

from labgraph_cpp import Node as _Node, NodeBootstrapInfo  # type: ignore

# HACK: Import from LabGraph's wrapper of Cthulhu before importing dynamic libs to set
# the shared memory name
from .._cthulhu import bindings  # noqa: F401
from ..messages.message import Message
from ..util.error import LabGraphError
from .config import Config
from .method import Subscriber, background
from .node import Node
from .state import State
from .stream import Stream
from .topic import Topic


class CPPNodeConfig(Config):
    args: List[Any] = field(default_factory=list)
    cpp_class: Optional[Type[_Node]] = None


class CPPNode(Node):
    config: CPPNodeConfig

    __cpp_node: Optional[_Node]

    def __init__(
        self, config: Optional[Config] = None, state: Optional[State] = None
    ) -> None:
        super().__init__(config=config, state=state)
        # We want to guarantee cpp_class is set on creation so that we can get topic
        # information from the C++ code
        assert config is not None
        assert config.cpp_class is not None
        self.__cpp_node = None

        topic_names = config.cpp_class.topic_names
        for topic_name in topic_names:
            assert topic_name not in self.__topics__.keys()
            topic = Topic(Message)
            setattr(self, topic_name, topic)
            self.__topics__[topic_name] = topic
            self.__streams__[topic_name] = Stream(
                id=topic_name, topic_paths=(topic_name,), message_type=Message
            )

    def _bootstrap(self, bootstrap_info: NodeBootstrapInfo) -> None:
        self._cpp_node._bootstrap(bootstrap_info)

    def configure(self, config: Config) -> None:
        # Because cpp_class is set on creation and we use it to get topic information
        # for this node, we don't want to overwrite it during configure(). We keep the
        # cpp_class fixed and just pass args through.
        assert isinstance(config, CPPNodeConfig)
        config = CPPNodeConfig(cpp_class=self.config.cpp_class, args=config.args)
        super().configure(config)

    @background
    async def run(self) -> None:
        import asyncio

        await asyncio.get_event_loop().run_in_executor(None, self._cpp_node.run)

    @property
    def _cpp_node(self) -> _Node:
        assert self.__cpp_node is not None
        return self.__cpp_node

    def setup(self) -> None:
        assert self.config.cpp_class is not None
        self.__cpp_node = self.config.cpp_class(*self.config.args)
        self._cpp_node.setup()

    def cleanup(self) -> None:
        try:
            self._cpp_node.cleanup()
        except AssertionError:
            # No CPP node (didn't bootstrap yet); this is fine
            pass

    @staticmethod
    def dummy_subscriber_method(message: Message) -> None:
        pass
