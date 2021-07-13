#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from abc import ABC, ABCMeta
from copy import deepcopy
from typing import Any, Callable, Dict, Optional, Set, Tuple, Type, TypeVar

import typeguard

from ..messages.message import Message
from ..util.error import LabGraphError
from ..util.random import random_string
from .config import Config
from .method import (
    Background,
    BackgroundType,
    Main,
    MainType,
    NodeMethod,
    Publisher,
    PublisherType,
    Subscriber,
    SubscriberType,
    Transformer,
    TransformerType,
)
from .state import State
from .stream import Stream
from .topic import PATH_DELIMITER, Topic


MODULE_ID_LENGTH = 16

T = TypeVar("T", bound=NodeMethod)  # TypeVar for NodeMethod return types


class ModuleMeta(ABCMeta):
    """
    Metaclass for module classes. See `Module` for what a module is. This
    metaclass is responsible for collecting the topic information from the class
    variables defined on the class.
    """

    __topics__: Dict[str, Topic]
    __state_type__: Type[State]
    __config_type__: Type[Config]

    # HACK: We take kwargs here because Python 3.6 passes an extra tvars
    # argument to the metaclass of a Generic. We can get rid of the kwargs
    # argument here in Python 3.7 which no longer passes this.
    def __init__(
        cls, name: str, bases: Tuple[type, ...], fields: Dict[str, Any], **kwargs: Any
    ) -> None:
        super(ModuleMeta, cls).__init__(name, bases, fields)

        cls.__topics__ = {}

        # Collect existing topics from base classes
        for base_cls in bases:
            for topic_name, topic in vars(base_cls).items():
                if not isinstance(topic, Topic):
                    continue

                # Raise if names of topics in multiple base classes collide
                if topic_name in cls.__topics__:
                    raise LabGraphError(
                        f"Base classes of {cls.__name__} have conflicting topics named "
                        f"{topic_name}"
                    )

                cls.__topics__[topic_name] = topic

        # Add the current class's topics
        for field_name, field_value in fields.items():
            if not isinstance(field_value, Topic):
                continue

            # Raise if a topic object was already used by a module (i.e., its _name) was
            # set
            if field_value._name is not None:
                raise LabGraphError(
                    "Duplicate topic object found: please assign different Topic "
                    f"objects to values {field_value.name} and {cls.__name__}."
                    f"{field_name}"
                )

            field_value._assign_name(field_name)

            # Raise if a topic name collides with a superclass's topic name
            if field_name in cls.__topics__:
                raise LabGraphError(
                    f"Topic {cls.__name__}/{field_name} hides superclass's topic"
                )

            cls.__topics__[field_name] = field_value

        cls.__state_type__: Type[State] = State
        cls.__config_type__: Type[Config] = Config
        if hasattr(cls, "__annotations__"):
            if "state" in cls.__annotations__:
                cls.__state_type__ = cls.__annotations__["state"]
            if "config" in cls.__annotations__:
                cls.__config_type__ = cls.__annotations__["config"]


class Module(ABC, metaclass=ModuleMeta):
    """
    An abstraction for a LabGraph component that can be run within a single process.
    """

    state: State
    _config: Optional[Config]
    __topics__: Dict[str, Topic]
    _id: str
    __children__: Dict[str, "Module"]
    __descendants__: Dict[str, "Module"]
    __streams__: Dict[str, Stream]
    __methods__: Dict[str, NodeMethod]

    def __init__(
        self, config: Optional[Config] = None, state: Optional[State] = None
    ) -> None:
        self.state = state or self.__class__.__state_type__()
        self._config = config
        self.__topics__ = deepcopy(self.__class__.__topics__)
        for topic_name, topic in self.__topics__.items():
            setattr(self, topic_name, topic)
        self._id = random_string(MODULE_ID_LENGTH)
        self.__children__ = {}
        self.__descendants__ = {}
        self.__streams__ = {}
        self.__methods__ = {}

    def setup(self) -> None:
        """
        Sets up the module. Subclasses can override to specify setup behavior that runs on
        graph startup.
        """
        pass

    def cleanup(self) -> None:
        """
        Cleans up the module. Subclasses can override to specify cleanup behavior that
        runs on graph termination.
        """
        pass

    def configure(self, config: Config) -> None:
        """
        Sets the configuration for this module.
        """
        self._config = config

    @property
    def is_configured(self) -> bool:
        return self._config is not None

    @property
    def config(self) -> Config:
        if self._config is None:
            try:
                # Try to create a default config with no arguments (would work with a
                # message type with fields that all have default values)
                self._config = self.__class__.__config_type__()
            except TypeError:
                raise LabGraphError(
                    f"Configuration not set. Call {self.__class__.__name__}.configure() to set the "
                    "configuration."
                )
        return self._config

    @property
    def id(self) -> str:
        """
        Returns a runtime identifier for the module.
        """
        return self._id

    def _get_method(self, method_path: str) -> Callable[..., Any]:
        """
        Returns the callable method in a node given a method path.

        Args:
            method_path: The path of the method to return.
        """
        assert method_path in self.__methods__.keys()
        node_path = PATH_DELIMITER.join(method_path.split(PATH_DELIMITER)[:-1])
        method_name = method_path.split(PATH_DELIMITER)[-1]
        if node_path == "":
            node = self
        else:
            node = self.__descendants__[node_path]
        return getattr(node, method_name)  # type: ignore

    def _get_subscriber_method(self, subscriber_path: str) -> SubscriberType:
        """
        Returns a callable subscriber method in a node given a subscriber path.

        Args:
            subscriber_path: The path of the subscriber method to return.
        """
        method = self._get_method(subscriber_path)
        typeguard.check_type(subscriber_path, method, SubscriberType)
        return method

    def _get_publisher_method(self, publisher_path: str) -> PublisherType:
        """
        Returns a callable publisher method in a node given a publisher path.

        Args:
            publisher_path: The path of the publisher method to return.
        """
        method = self._get_method(publisher_path)
        typeguard.check_type(publisher_path, method, PublisherType)
        return method

    def _get_background_method(self, background_path: str) -> BackgroundType:
        """
        Returns a callable background method in a node given a background path.

        Args:
            background_path: The path of the background method to return.
        """
        method = self._get_method(background_path)
        typeguard.check_type(background_path, method, BackgroundType)
        return method

    def _get_main_method(self, main_path: str) -> MainType:
        """
        Returns a callable main method in a node given a main path.

        Args:
            main_path: The path of the main method to return.
        """
        method = self._get_method(main_path)
        typeguard.check_type(main_path, method, MainType)
        return method

    def _get_transformer_method(self, transformer_path: str) -> TransformerType:
        """
        Returns a callable transformer method in a node given a transformer path.

        Args:
            transformer_path: The path of the transformer method to return.
        """
        method = self._get_method(transformer_path)
        typeguard.check_type(transformer_path, method, TransformerType)
        return method

    def _get_streams_by_logging_id(self) -> Dict[str, Stream]:
        """
        Returns a dictionary where each entry is a global logging identifier
        for its associated `Stream`.

        Since logging identifiers are meant to be global, they are only
        valid to define on a `Graph` and not a `Module` or `Group`.
        """
        return {}

    def _get_methods_of_type(self, method_type: Type[T]) -> Dict[str, T]:
        return {
            method_path: method
            for method_path, method in self.__methods__.items()
            if isinstance(method, method_type)
        }

    @property
    def publishers(self) -> Dict[str, Publisher]:
        """
        Returns the publishers of this group's nodes.
        """
        return self._get_methods_of_type(Publisher)

    @property
    def subscribers(self) -> Dict[str, Subscriber]:
        """
        Returns the subscribers of this group's nodes.
        """
        return self._get_methods_of_type(Subscriber)

    @property
    def transformers(self) -> Dict[str, Transformer]:
        """
        Returns the transformers of this group's nodes.
        """
        return self._get_methods_of_type(Transformer)

    @property
    def backgrounds(self) -> Dict[str, Background]:
        """
        Returns the background methods of this group's nodes.
        """
        return self._get_methods_of_type(Background)

    @property
    def main(self) -> Tuple[Optional[str], Optional[Main]]:
        """
        Returns the main method of this module, if any. The return value is a tuple of
        the method path and the method. If there is no main method, this returns
        `(None, None)`.
        """
        main_methods = self._get_methods_of_type(Main)
        if len(main_methods) > 1:
            method_names = ", ".join(main_methods.keys())
            raise LabGraphError(
                "Cannot have multiple methods decorated with @main in nodes in the "
                f"same process: found methods {method_names}"
            )
        if len(main_methods) == 0:
            return (None, None)

        return next(iter(main_methods.items()))

    def _stream_for_topic_path(self, topic_path: str) -> Stream:
        """
        Returns the stream the topic at `topic_path` is in.
        """
        for stream in self.__streams__.values():
            if topic_path in stream.topic_paths:
                return stream
        raise LabGraphError(f"Topic '{topic_path}' is not in a stream")

    def _get_topic_path(self, topic: Topic) -> str:
        """
        Given a `Topic` object, returns the path to the topic in this module.
        """
        for topic_path, candidate_topic in self.__topics__.items():
            if topic is candidate_topic:
                return topic_path

        raise LabGraphError(
            f"Could not find topic '{topic.name}' in module {self.__class__.__name__}"
        )

    def _get_module_path(self, module: "Module") -> str:
        """
        Given a `Module` object, returns the path to the descendant module of this
        module.
        """
        for module_path, candidate_module in self.__descendants__.items():
            if not isinstance(candidate_module, Module):
                continue
            if candidate_module is module:
                return module_path

        raise LabGraphError(
            f"Could not find module '{module.__class__.__name__}' ({module.id}) in "
            f"module {self.__class__.__name__}"
        )

    @property
    def message_types(self) -> Set[Type[Message]]:
        """
        Returns the message types used by this module's topics.
        """
        return {topic.message_type for topic in self.__topics__.values()}

    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.id})"

    def _validate_streams(self) -> None:
        """
        Performs validation of the streams in this group:
        - guarantees that each stream has only one publisher
        """
        for stream in self.__streams__.values():
            publisher_paths = set()
            for topic_path in stream.topic_paths:
                for method_path, method in self.__methods__.items():
                    if (
                        isinstance(method, Publisher)
                        and topic_path in method.published_topic_paths
                    ):
                        publisher_paths.add(method_path)
            if len(publisher_paths) > 1:
                error_message = (
                    f"The stream for topics ({', '.join(sorted(stream.topic_paths))}) "
                    "has multiple publishers, but only one publisher is allowed. The "
                    "following publishers were found:\n"
                )
                error_message += "\n".join(
                    sorted(f"- {path}" for path in publisher_paths)
                )
                raise LabGraphError(error_message)
