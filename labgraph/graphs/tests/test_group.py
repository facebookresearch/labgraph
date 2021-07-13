#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Any, Dict, Set, Tuple, Type

import pytest

from ...messages.message import Message
from ...util.error import LabGraphError
from ..group import Connections, Group
from ..method import AsyncPublisher, NodeMethod, Transformer, publisher, subscriber
from ..module import Module
from ..node import Node
from ..topic import PATH_DELIMITER, Topic


class MyMessage(Message):
    int_field: int


class MyMessage2(Message):
    int_field: int


class MyNode(Node):
    A = Topic(MyMessage)
    B = Topic(MyMessage)

    @subscriber(A)
    @publisher(B)
    def my_transformer(self, message: MyMessage) -> AsyncPublisher:
        pass


class MyChildGroup(Group):
    C = Topic(MyMessage)
    MY_NODE1: MyNode
    MY_NODE2: MyNode

    def connections(self) -> Connections:
        return ((self.C, self.MY_NODE1.A), (self.MY_NODE1.B, self.MY_NODE2.A))


class MyParentGroup(Group):
    D = Topic(MyMessage)
    E = Topic(MyMessage2)
    MY_CHILD1: MyChildGroup
    MY_CHILD2: MyChildGroup

    def connections(self) -> Connections:
        return ((self.D, self.MY_CHILD1.C), (self.E, self.MY_CHILD2.MY_NODE1.A))


class MySubclassGroup(MyParentGroup):
    F = Topic(MyMessage2)

    def connections(self) -> Connections:
        return (
            (self.D, self.MY_CHILD1.C),
            (self.E, self.MY_CHILD2.MY_NODE1.A),
            (self.E, self.F),
        )


parent_group = MyParentGroup()

expected_streams = (
    (
        parent_group,
        (
            ("D", "MY_CHILD1/C", "MY_CHILD1/MY_NODE1/A"),
            ("E", "MY_CHILD2/C", "MY_CHILD2/MY_NODE1/A"),
            ("MY_CHILD1/MY_NODE1/B", "MY_CHILD1/MY_NODE2/A"),
            ("MY_CHILD1/MY_NODE2/B",),
            ("MY_CHILD2/MY_NODE1/B", "MY_CHILD2/MY_NODE2/A"),
            ("MY_CHILD2/MY_NODE2/B",),
        ),
    ),
    (
        parent_group.MY_CHILD1,
        (("C", "MY_NODE1/A"), ("MY_NODE1/B", "MY_NODE2/A"), ("MY_NODE2/B",)),
    ),
    (
        parent_group.MY_CHILD2,
        (("C", "MY_NODE1/A"), ("MY_NODE1/B", "MY_NODE2/A"), ("MY_NODE2/B",)),
    ),
)


@pytest.mark.parametrize("group,streams", expected_streams)  # type: ignore
def test_group_streams(group: Group, streams: Tuple[Tuple[str, ...], ...]) -> None:
    stream_paths = tuple(
        sorted(stream.topic_paths for stream in group.__streams__.values())
    )
    assert stream_paths == streams


expected_descendants = (
    (
        parent_group.MY_CHILD1,
        {
            "MY_NODE1": parent_group.MY_CHILD1.MY_NODE1,
            "MY_NODE2": parent_group.MY_CHILD1.MY_NODE2,
        },
    ),
    (
        parent_group,
        {
            "MY_CHILD1": parent_group.MY_CHILD1,
            "MY_CHILD2": parent_group.MY_CHILD2,
            "MY_CHILD1/MY_NODE1": parent_group.MY_CHILD1.MY_NODE1,
            "MY_CHILD1/MY_NODE2": parent_group.MY_CHILD1.MY_NODE2,
            "MY_CHILD2/MY_NODE1": parent_group.MY_CHILD2.MY_NODE1,
            "MY_CHILD2/MY_NODE2": parent_group.MY_CHILD2.MY_NODE2,
        },
    ),
)


@pytest.mark.parametrize("group,descendants", expected_descendants)  # type: ignore
def test_group_descendants(group: Group, descendants: Dict[str, Any]) -> None:
    assert group.__descendants__ == descendants


expected_children = (
    (
        parent_group.MY_CHILD1,
        {
            "MY_NODE1": parent_group.MY_CHILD1.MY_NODE1,
            "MY_NODE2": parent_group.MY_CHILD1.MY_NODE2,
        },
    ),
    (
        parent_group,
        {"MY_CHILD1": parent_group.MY_CHILD1, "MY_CHILD2": parent_group.MY_CHILD2},
    ),
)


@pytest.mark.parametrize("group,children", expected_children)  # type: ignore
def test_group_children(group: Group, children: Dict[str, Module]) -> None:
    assert group.__children__ == children


expected_methods = (
    (
        parent_group.MY_CHILD1,
        {
            "MY_NODE1/my_transformer": Transformer(
                name="my_transformer",
                published_topic_paths=("MY_NODE1/B",),
                subscribed_topic_path="MY_NODE1/A",
            ),
            "MY_NODE2/my_transformer": Transformer(
                name="my_transformer",
                published_topic_paths=("MY_NODE2/B",),
                subscribed_topic_path="MY_NODE2/A",
            ),
        },
    ),
    (
        parent_group,
        {
            "MY_CHILD1/MY_NODE1/my_transformer": Transformer(
                name="my_transformer",
                published_topic_paths=("MY_CHILD1/MY_NODE1/B",),
                subscribed_topic_path="MY_CHILD1/MY_NODE1/A",
            ),
            "MY_CHILD1/MY_NODE2/my_transformer": Transformer(
                name="my_transformer",
                published_topic_paths=("MY_CHILD1/MY_NODE2/B",),
                subscribed_topic_path="MY_CHILD1/MY_NODE2/A",
            ),
            "MY_CHILD2/MY_NODE1/my_transformer": Transformer(
                name="my_transformer",
                published_topic_paths=("MY_CHILD2/MY_NODE1/B",),
                subscribed_topic_path="MY_CHILD2/MY_NODE1/A",
            ),
            "MY_CHILD2/MY_NODE2/my_transformer": Transformer(
                name="my_transformer",
                published_topic_paths=("MY_CHILD2/MY_NODE2/B",),
                subscribed_topic_path="MY_CHILD2/MY_NODE2/A",
            ),
        },
    ),
)


@pytest.mark.parametrize("group,methods", expected_methods)  # type: ignore
def test_group_methods(group: Group, methods: Dict[str, NodeMethod]) -> None:
    for method_path, method in methods.items():
        assert isinstance(group.__methods__[method_path], type(method))
        assert vars(group.__methods__[method_path]) == vars(method)


expected_topics = (
    (
        parent_group.MY_CHILD1,
        {"C", "MY_NODE1/A", "MY_NODE1/B", "MY_NODE2/A", "MY_NODE2/B"},
    ),
    (
        parent_group,
        {
            "D",
            "E",
            "MY_CHILD1/C",
            "MY_CHILD1/MY_NODE1/A",
            "MY_CHILD1/MY_NODE1/B",
            "MY_CHILD1/MY_NODE2/A",
            "MY_CHILD1/MY_NODE2/B",
            "MY_CHILD2/C",
            "MY_CHILD2/MY_NODE1/A",
            "MY_CHILD2/MY_NODE1/B",
            "MY_CHILD2/MY_NODE2/A",
            "MY_CHILD2/MY_NODE2/B",
        },
    ),
)


@pytest.mark.parametrize("group,topics", expected_topics)  # type: ignore
def test_group_topics(group: Group, topics: Set[str]) -> None:
    for topic_name in topics:
        topic = group.__topics__[topic_name]
        if PATH_DELIMITER not in topic_name:
            assert getattr(group, topic_name) is topic
        assert topic.name == topic_name.split(PATH_DELIMITER)[-1]
        assert topic.message_type == MyMessage


class BadPublishersNode(Node):
    A = Topic(MyMessage)

    @publisher(A)
    async def pub(self) -> AsyncPublisher:
        yield self.A, MyMessage(int_field=1)


class BadPublishersGroup(Group):
    NODE1: BadPublishersNode
    NODE2: BadPublishersNode

    def connections(self) -> Connections:
        return ((self.NODE1.A, self.NODE2.A),)


def test_bad_publishers_group() -> None:
    with pytest.raises(LabGraphError) as err:
        _ = BadPublishersGroup()

    assert (
        "The stream for topics (NODE1/A, NODE2/A) has multiple publishers, but only "
        "one publisher is allowed. The following publishers were found:\n"
        "- NODE1/pub\n"
        "- NODE2/pub" in str(err.value)
    )


class BadConnectionsGroup1(Group):
    def connections(self) -> Connections:
        return 5  # type: ignore


class BadConnectionsGroup2(Group):
    A = Topic(MyMessage)
    B = Topic(MyMessage)

    def connections(self) -> Connections:
        return (self.A, self.B)  # type: ignore


class BadConnectionsGroup3(Group):
    A = Topic(MyMessage)
    B = Topic(MyMessage)
    C = Topic(MyMessage)

    def connections(self) -> Connections:
        return ((self.A, self.B, self.C),)  # type: ignore


@pytest.mark.parametrize(
    "group_type", (BadConnectionsGroup1, BadConnectionsGroup2, BadConnectionsGroup3)
)
def test_bad_connections_group(group_type: Type[Group]) -> None:
    with pytest.raises(TypeError) as err:
        group = group_type()


def test_subclass_group() -> None:
    subclass_group = MySubclassGroup()
