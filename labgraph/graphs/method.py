#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    List,
    Optional,
    Sequence,
    Tuple,
)

from typing_extensions import Protocol

from ..util.error import LabgraphError
from .topic import Topic


_METADATA_LABEL = "_METADATA"


class AsyncPublisher(Protocol):
    """
    Convenience return type for async publisher methods. An async method that yields
    tuples of Labgraph topics and messages can be typed as returning this.
    For example:

    ```
    import labgraph as lg
    ...
    class MyNode(Node):
        A = Topic(MyMessage)

        @publisher(A)
        def publisher_method(self) -> lg.AsyncPublisher:
            ...
            yield self.A, message
            ...
    ```
    """

    def __aiter__(self) -> AsyncIterator[Tuple[Topic, Any]]:
        ...


PublisherType = Callable[..., AsyncPublisher]
SubscriberType = Callable[..., Any]
TransformerType = Callable[..., AsyncPublisher]
BackgroundType = Callable[..., Awaitable[None]]
MainType = Callable[..., None]


class NodeMethod(ABC):
    """
    Represents a method on a Node that has been decorated by Labgraph. Subclasses
    include topic paths, if applicable.
    """

    name: str

    @abstractmethod
    def __init__(self, name: str) -> None:
        self.name = name


@dataclass
class MethodMetadata:
    """
    Represents metadata on a method that is created by a Labgraph decorator. The
    `MethodMetadata` is used to validate the decorator usage and then construct a
    `NodeMethod`.
    """

    name: str
    published_topics: List[Topic] = field(default_factory=list)
    subscribed_topic: Optional[Topic] = None
    is_background: bool = False
    is_main: bool = False

    @property
    def node_method(self) -> NodeMethod:
        """
        Constructs a `NodeMethod` using this metadata. The `NodeMethod` uses topic paths
        instead of `Topic` objects.
        """
        self.validate()

        if len(self.published_topics) > 0 and self.subscribed_topic is not None:
            return Transformer(
                name=self.name,
                published_topic_paths=tuple(
                    topic.name for topic in self.published_topics
                ),
                subscribed_topic_path=self.subscribed_topic.name
                if self.subscribed_topic is not None
                else None,
            )
        elif len(self.published_topics) > 0:
            return Publisher(
                name=self.name,
                published_topic_paths=tuple(
                    topic.name for topic in self.published_topics
                ),
            )
        elif self.subscribed_topic is not None:
            return Subscriber(
                name=self.name,
                subscribed_topic_path=self.subscribed_topic.name
                if self.subscribed_topic is not None
                else None,
            )
        elif self.is_background:
            return Background(name=self.name)
        elif self.is_main:
            return Main(name=self.name)
        else:
            raise LabgraphError("Unexpected NodeMethod type")

    def validate(self) -> None:
        for i, topic1 in enumerate(self.published_topics):
            for j, topic2 in enumerate(self.published_topics):
                if i != j and topic1 is topic2:
                    raise LabgraphError(
                        f"Method '{self.name}' got two @publisher decorators for the "
                        "same topic"
                    )

        if len(self.published_topics) > 0:
            if self.is_background:
                raise LabgraphError(
                    f"Method '{self.name}' cannot have both a @{publisher.__name__} "
                    f"decorator and a @{background.__name__} decorator"
                )
            if self.is_main:
                raise LabgraphError(
                    f"Method '{self.name}' cannot have both a @{publisher.__name__} "
                    f"decorator and a @{main.__name__} decorator"
                )

        if self.subscribed_topic is not None:
            if self.is_background:
                raise LabgraphError(
                    f"Method '{self.name}' cannot have both a @{subscriber.__name__} "
                    f"decorator and a @{background.__name__} decorator"
                )
            if self.is_main:
                raise LabgraphError(
                    f"Method '{self.name}' cannot have both a @{subscriber.__name__} "
                    f"decorator and a @{main.__name__} decorator"
                )

        if self.is_background and self.is_main:
            raise LabgraphError(
                f"Method '{self.name}' cannot have both a @{background.__name__} "
                f"decorator and a @{main.__name__} decorator"
            )


def get_method_metadata(method: Callable[..., Any]) -> MethodMetadata:
    """
    Returns the `MethodMetadata` associated with a method, creating one if it doesn't
    already exist.
    """
    metadata: MethodMetadata
    if hasattr(method, _METADATA_LABEL):
        metadata = getattr(method, _METADATA_LABEL)
        assert isinstance(metadata, MethodMetadata)
    else:
        metadata = MethodMetadata(name=method.__name__)
        setattr(method, _METADATA_LABEL, metadata)
    return metadata


class Publisher(NodeMethod):
    """
    Represents a Labgraph method decorated by `@publisher`.
    """

    published_topic_paths: Tuple[str, ...]

    def __init__(self, name: str, published_topic_paths: Sequence[str]) -> None:
        NodeMethod.__init__(self, name)
        self.published_topic_paths = tuple(published_topic_paths)


def publisher(topic: Topic) -> Callable[[PublisherType], PublisherType]:
    """
    Decorator for methods on a `Node` subclass. `@publisher(T)` causes the method to be
    able to publish to the topic `T`.
    """

    def publisher_wrapper(method: PublisherType) -> PublisherType:
        metadata = get_method_metadata(method)
        metadata.published_topics.append(topic)
        metadata.validate()
        return method

    return publisher_wrapper


class Subscriber(NodeMethod):
    """
    Represents a Labgraph method decorated by `@subscriber`.
    """

    subscribed_topic_path: str

    def __init__(self, name: str, subscribed_topic_path: str) -> None:
        NodeMethod.__init__(self, name)
        self.subscribed_topic_path = subscribed_topic_path


def subscriber(topic: Topic) -> Callable[[SubscriberType], SubscriberType]:
    """
    Decorator for methods on a `Node` subclass. `@subscriber(T)` causes the method to be
    subscribed to the topic `T`.
    """

    def subscriber_wrapper(method: SubscriberType) -> SubscriberType:
        annotations = {
            arg: arg_type
            for arg, arg_type in method.__annotations__.items()
            if arg not in ("self", "return")
        }
        if (
            not len(annotations) == 1
            or list(annotations.values())[0] != topic.message_type
            or method.__code__.co_argcount != 2
            or method.__code__.co_varnames[0] != "self"
            or method.__code__.co_varnames[1] != list(annotations.keys())[0]
            # TODO: We could also check the return type here
        ):
            raise LabgraphError(
                f"Expected subscriber '{method.__name__}' to have signature def "
                f"{method.__name__}(self, message: {topic.message_type.__name__}) -> "
                "None"
            )

        metadata = get_method_metadata(method)
        if metadata.subscribed_topic is not None:
            raise LabgraphError(
                f"Method '{metadata.name}' already has a @{subscriber.__name__} "
                "decorator"
            )

        metadata.subscribed_topic = topic
        metadata.validate()
        return method

    return subscriber_wrapper


class Transformer(Publisher, Subscriber):
    """
    Represents a Labgraph method decorated by both `@publisher` and `@subscriber`.
    """

    def __init__(
        self,
        name: str,
        published_topic_paths: Sequence[str],
        subscribed_topic_path: str,
    ) -> None:
        Publisher.__init__(self, name, published_topic_paths)
        Subscriber.__init__(self, name, subscribed_topic_path)


class Background(NodeMethod):
    """
    Represents a Labgraph method decorated by `@background`.
    """

    def __init__(self, name: str) -> None:
        super(Background, self).__init__(name)


def background(method: BackgroundType) -> BackgroundType:
    """
    Decorator for methods on a `Node` subclass. Adding `@background` causes the
    method to be run in a background event loop when the node starts up. The method
    cannot also be a subscriber or publisher. This is useful for methods that don't
    interact with topics - for example, UI-related methods.
    """
    metadata = get_method_metadata(method)
    if metadata.is_background:
        raise LabgraphError(
            f"Method '{metadata.name}' already has a @{background.__name__} decorator"
        )
    metadata.is_background = True
    metadata.validate()
    return method


class Main(NodeMethod):
    """
    Represents a Labgraph method decorated by `@main`.
    """

    def __init__(self, name: str) -> None:
        super(Main, self).__init__(name)


def main(method: MainType) -> MainType:
    """
    Decorator for methods on a `Node` subclass. Adding `@main` causes the
    method to be run in the main thread when the graph starts up. The method cannot also
    be a subscriber or publisher. This is useful for methods that don't interact with
    topics - for example, UI-related methods. Each node can only have one method
    decorated by `@main`.
    """
    metadata = get_method_metadata(method)
    if metadata.is_main:
        raise LabgraphError(
            f"Method '{metadata.name}' already has a @{main.__name__} decorator"
        )
    metadata.is_main = True
    metadata.validate()
    return method
