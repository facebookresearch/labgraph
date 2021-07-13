#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import logging
from collections.abc import Iterable
from copy import deepcopy
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Type, Union

import typeguard
from labgraph_cpp import Node as _Node  # type: ignore
from typing_extensions import Protocol, runtime_checkable

# HACK: Import from LabGraph's wrapper of Cthulhu before importing dynamic libs to set
# the shared memory name
from .._cthulhu import bindings as cthulhu  # noqa: F401
from ..messages.message import Message
from ..util.error import LabGraphError
from .config import Config
from .cpp_node import CPPNode, CPPNodeConfig
from .method import Main, Publisher, Subscriber
from .module import Module, ModuleMeta
from .node import Node
from .state import State
from .stream import Stream
from .topic import PATH_DELIMITER, Topic


Connections = Sequence[Tuple[Topic, Topic]]
logger = logging.getLogger(__name__)


class GroupMeta(ModuleMeta):
    """
    Metaclass for `Group` classes. This metaclass is responsible for reading the
    children of the group (`Node`s and other `Group`s) from the class variables
    and storing them.
    """

    __children_types__: Dict[str, Union[Type[Module], Type[_Node]]]

    # HACK: We take kwargs here because Python 3.6 passes an extra tvars
    # argument to the metaclass of a Generic. We can get rid of the kwargs
    # argument here in Python 3.7 which no longer passes this.
    def __init__(
        cls, name: str, bases: Tuple[type, ...], fields: Dict[str, Any], **kwargs: Any
    ) -> None:
        super(GroupMeta, cls).__init__(name, bases, fields)

        # Collect the group's children types
        cls.__children_types__ = {}
        if hasattr(cls, "__annotations__"):
            for field_name, field_type in cls.__annotations__.items():
                if isinstance(field_type, type) and (
                    issubclass(field_type, Module) or issubclass(field_type, _Node)
                ):
                    cls.__children_types__[field_name] = field_type


class Group(Module, metaclass=GroupMeta):
    """
    Represents a group in a graph. A group defines a collection of nodes and
    other groups. By overriding `connections()` a group can link the topics of
    its children in order to set up communications.
    """

    def __init__(
        self, config: Optional[Config] = None, state: Optional[State] = None
    ) -> None:
        super(Group, self).__init__(config=config, state=state)

        # Collect the group's children (as instances)
        for child_name, child_type in self.__class__.__children_types__.items():
            if not self._is_valid_child_name(child_name):
                continue
            if issubclass(child_type, _Node):
                cpp_node = CPPNode(config=CPPNodeConfig(cpp_class=child_type))
                self.__children__[child_name] = cpp_node
            else:
                self.__children__[child_name] = child_type()

        for child_name, child in self.__children__.items():
            setattr(self, child_name, child)

        # Collect the group's descendants (children + recursive children of
        # child groups)
        for child_name, child in self.__children__.items():
            self.__descendants__[child_name] = child
        for child_name, child in self.__children__.items():
            if isinstance(child, Group):
                for descendant_path, descendant in child.__descendants__.items():
                    self.__descendants__[
                        PATH_DELIMITER.join((child_name, descendant_path))
                    ] = descendant

            # Collect the group's descendants' topics
            if isinstance(child, Group) or isinstance(child, Node):
                for topic_path, topic in child.__topics__.items():
                    self.__topics__[
                        PATH_DELIMITER.join((child_name, topic_path))
                    ] = topic

        # Collect the group's node methods
        for descendant_path, descendant in self.__descendants__.items():
            if isinstance(descendant, Node):
                for method_name, method in descendant.__methods__.items():
                    new_method = deepcopy(method)
                    if isinstance(new_method, Publisher):
                        new_method.published_topic_paths = tuple(
                            PATH_DELIMITER.join((descendant_path, topic_path))
                            for topic_path in new_method.published_topic_paths
                        )
                    if isinstance(new_method, Subscriber):
                        new_method.subscribed_topic_path = PATH_DELIMITER.join(
                            (descendant_path, new_method.subscribed_topic_path)
                        )
                    self.__methods__[
                        PATH_DELIMITER.join((descendant_path, method_name))
                    ] = new_method

        # Collect the group's stream information
        self.__streams__ = self._get_streams()

        # Update the descendants' stream information so that connected topics have the
        # same backing stream
        self._update_descendant_streams()

        # Ensure the connections of this group didn't create any streams with multiple
        # publishers
        self._validate_streams()

    def _get_streams(self) -> Dict[str, Stream]:
        """
        Returns a dictionary containing a stream for each group of topics that are
        joined to each other. Topic joins are transitive, i.e., if A is joined to B, and
        B is joined to C, then A is joined to C.
        """

        # This is basically a version of the union-find algorithm. We start by putting
        # each topic in its own stream, then for each topic pair that is joined, we merge
        # each topics' stream.

        stream_nums: Dict[str, int] = {}

        for topic_name in self.__topics__.keys():
            if PATH_DELIMITER not in topic_name:
                # Put each topic in this group in its own stream
                stream_nums[topic_name] = len(stream_nums)

        for child_name, child in self.__children__.items():
            # Preserve the streams that child modules have already computed
            for stream in child.__streams__.values():
                new_stream_num = len(stream_nums)
                for topic_path in stream.topic_paths:
                    stream_nums[
                        PATH_DELIMITER.join((child_name, topic_path))
                    ] = new_stream_num

        # Use `connections()` to merge streams
        connections = list(self.connections())
        typeguard.check_type(
            f"{self.__class__.__name__}.{self.connections.__name__}()",
            connections,
            Connections,
        )
        for topic1, topic2 in connections:
            # Find the topic paths for these `Topic` objects
            topic_paths: List[str] = []
            for topic in (topic1, topic2):
                for topic_path, descendant_topic in self.__topics__.items():
                    if topic is descendant_topic:
                        topic_paths.append(topic_path)
                        break

            assert len(topic_paths) == 2

            # Set the stream numbers of all topics in the two old streams to be
            # the same
            old_stream_nums = (stream_nums[topic_paths[0]], stream_nums[topic_paths[1]])
            new_stream_num = min(old_stream_nums)
            for topic_path, stream_num in list(stream_nums.items()):
                if stream_num in old_stream_nums:
                    stream_nums[topic_path] = new_stream_num

        # Group the topics by stream number, validate their message types, and sort the
        # topic names in each stream
        result = []
        for stream_num in set(stream_nums.values()):
            topic_paths = sorted(p for p, n in stream_nums.items() if n == stream_num)

            message_types_by_topic: Dict[str, Type[Message]] = {}
            for topic_path in topic_paths:
                message_types_by_topic[topic_path] = self.__topics__[
                    topic_path
                ].message_type

            message_types = list(message_types_by_topic.values())
            # Use == to unique instead of creating a set() which compares via `is`
            message_types = [
                m for i, m in enumerate(message_types) if message_types.index(m) == i
            ]

            # HACK: Since we don't currently use Cthulhu dynamic types, we don't know
            # what types a CPPNode's topics use. We type them as Message for now, and
            # exclude them from the topics-have-same-type check below.
            for message_type in list(message_types):
                if message_type is Message:
                    message_types.remove(message_type)

            if len(message_types) > 1:
                error_message = (
                    "Topics in stream must have matching message types, found the "
                    "following types for the same stream:\n"
                )
                for topic_path in topic_paths:
                    error_message += (
                        f"- {topic_path}: {message_types_by_topic[topic_path]}\n"
                    )
                raise LabGraphError(error_message)

            if len(message_types) == 0:
                warning_message = (
                    "Found no message types for a stream. This could be because the "
                    "topic is never used in Python. Consume a topic with a message "
                    "type in Python to make this stream work. This stream contains the "
                    "following topics:\n"
                )
                for topic_path in topic_paths:
                    warning_message += f"- {topic_path}\n"

                logger.warning(warning_message)

                result.append(Stream(topic_paths=tuple(topic_paths)))
            else:
                # The stream is valid, so create the stream object
                result.append(
                    Stream(
                        topic_paths=tuple(topic_paths),
                        message_type=list(message_types)[0],
                    )
                )

        # Index the streams by id
        return {stream.id: stream for stream in result}

    def _update_descendant_streams(self) -> None:
        """
        Updates the descendants' streams so that connected topics have the same
        underlying streams.
        """
        for module_path, module in self.__descendants__.items():
            streams = {
                stream.id: stream
                for stream in self.__streams__.values()
                if any(
                    topic_path.startswith(module_path)
                    for topic_path in stream.topic_paths
                )
            }
            module_streams = {
                stream.id: Stream(
                    id=stream.id,
                    message_type=stream.message_type,
                    topic_paths=tuple(
                        topic_path[len(module_path) + len(PATH_DELIMITER) :]
                        for topic_path in stream.topic_paths
                        if topic_path.startswith(module_path)
                    ),
                )
                for stream in streams.values()
            }
            module.__streams__ = module_streams

    def connections(self) -> "Connections":
        """
        Override `connections` in order to specify which topics in this group should
        be joined to each other. Topics that are joined together will be backed by the
        same stream. This is intended to be used to connect different children of this
        group together. For example, if node `N` publishes to topic `A` and
        group `C` subscribes to topic `B`, we can return `((self.N.A, self.C.B),)`
        here to connect `N`'s output to `C`'s input.
        """
        return ()  # Return no connections by default

    def _is_valid_child_name(self, name: str) -> bool:
        """
        Returns true if the given name is valid for a child of this group. Notably,
        returns false for LabGraph-internal fields starting with "__" as well as
        special fields like `config`.
        """
        if name.startswith("__"):
            return False
        SPECIAL_NAMES = ("config", "state")
        if name in SPECIAL_NAMES:
            return False
        return True
