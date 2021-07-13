#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from copy import deepcopy
from typing import Any, Dict, Optional, Tuple

from ..util.error import LabGraphError
from .config import Config
from .method import _METADATA_LABEL, NodeMethod, get_method_metadata
from .module import Module, ModuleMeta
from .state import State
from .stream import Stream


class NodeMeta(ModuleMeta):
    """
    Metaclass for Node classes. This metaclass is responsible for reading the decorators
    on a Node subclass and producing `NodeMethod` objects which are descriptions of the
    decorated methods that type of node has. These objects are propagated to the node's
    ancestors when an instance is added to a graph.
    """

    __methods__: Dict[str, NodeMethod]

    # HACK: We take kwargs here because Python 3.6 passes an extra tvars
    # argument to the metaclass of a Generic. We can get rid of the kwargs
    # argument here in Python 3.7 which no longer passes this.
    def __init__(
        cls, name: str, bases: Tuple[type, ...], fields: Dict[str, Any], **kwargs: Any
    ) -> None:
        super(NodeMeta, cls).__init__(name, bases, fields)

        if hasattr(cls, "__methods__"):
            # Copy methods from superclass
            cls.__methods__ = {**cls.__methods__}
        else:
            cls.__methods__ = {}

        # Collect metadata created by decorators on the node's methods
        for field_name, field_value in fields.items():
            if callable(field_value) and hasattr(field_value, _METADATA_LABEL):
                metadata = get_method_metadata(field_value)

                published_topics = metadata.published_topics
                subscribed_topic = metadata.subscribed_topic

                # Validate the topic objects provided to @publisher and @subscriber
                # decorators
                for topic in published_topics + (
                    [subscribed_topic] if subscribed_topic is not None else []
                ):
                    if topic._name is None or topic.name not in cls.__topics__.keys():
                        topic_verb = (
                            "subscribed to"
                            if topic is subscribed_topic
                            else "published"
                        )
                        raise LabGraphError(
                            f"Invalid topic {topic_verb} by {cls.__name__}."
                            f"{field_name} - set the topic as a class variable "
                            f"in {cls.__name__}"
                        )

                # Validate that there are not multiple @main decorators
                if metadata.is_main:
                    other_methods = {
                        n: v
                        for n, v in fields.items()
                        if callable(v)
                        and hasattr(v, _METADATA_LABEL)
                        and n != field_name
                    }

                    for other_method_name, other_method in other_methods.items():
                        if get_method_metadata(other_method).is_main:
                            raise LabGraphError(
                                f"Cannot have multiple methods decorated with @main in "
                                f"{name}: found methods '{field_name}' and "
                                f"'{other_method_name}'"
                            )

                # Validation complete: add the method to the node class
                cls.__methods__[field_name] = metadata.node_method


class Node(Module, metaclass=NodeMeta):
    """
    Represents a node in a graph. A user can instantiate this to define computation that
    always occurs within the same process in a graph. Since nodes are modules,
    topics can be added to nodes as class variables. Nodes can then use the @publisher
    and @subscriber decorators to describe how the node's methods interact with those
    topics.

    A method with a @subscriber(T) decorator is called with a message whenever
    the topic T receives that message. A method with a @publisher(T) decorator must be
    defined as async and can yield T, M to publish message M to topic T. A method can
    subscribe to at most one topic but can publish to any number of topics via multiple
    decorators.

    A method with one or more @publisher decorators but no @subscriber decorator is
    considered an entry point of the graph and will be called at graph startup.
    """

    def __init__(
        self, config: Optional[Config] = None, state: Optional[State] = None
    ) -> None:
        super(Node, self).__init__(config=config, state=state)

        self.__methods__ = deepcopy(self.__class__.__methods__)

        for topic_name, topic in self.__topics__.items():
            setattr(self, topic_name, topic)

            stream = Stream(topic_paths=(topic_name,), message_type=topic.message_type)
            self.__streams__[stream.id] = stream

        self._validate_streams()
