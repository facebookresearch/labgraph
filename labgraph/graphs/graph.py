#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Any, Dict, Optional, Sequence, Tuple

from ..util.error import LabGraphError
from ..util.logger import get_logger
from .config import Config
from .group import Group, GroupMeta
from .module import Module
from .node import Node
from .state import State
from .stream import Stream
from .topic import Topic


logger = get_logger(__name__)


class GraphMeta(GroupMeta):
    # HACK: We take kwargs here because Python 3.6 passes an extra tvars
    # argument to the metaclass of a Generic. We can get rid of the kwargs
    # argument here in Python 3.7 which no longer passes this.
    def __init__(
        cls, name: str, bases: Tuple[type, ...], fields: Dict[str, Any], **kwargs: Any
    ) -> None:
        super(GraphMeta, cls).__init__(name, bases, fields)

        if hasattr(cls, "__annotations__"):
            if "config" in cls.__annotations__:
                if not issubclass(cls.__annotations__["config"], Config):
                    raise LabGraphError(
                        "The config for a Graph must be a subclass of Config, got "
                        f"{cls.__annotations__['config']}"
                    )


class Graph(Group, metaclass=GraphMeta):
    """
    Represents a computational graph. A graph is simply a group that validates that
    all of its topics have publishers and subscribers.
    """

    config: Config

    def __init__(
        self, config: Optional[Config] = None, state: Optional[State] = None
    ) -> None:
        super(Graph, self).__init__(config=config, state=state)

        self._validate_topics()

    def _validate_topics(self) -> None:
        """
        Validates all the graph's topics have publishers and subscribers. Raises an
        error if any topic lacks a publisher or subscriber.
        """
        stream_is_published = {
            stream_id: False for stream_id in self.__streams__.keys()
        }
        stream_is_subscribed = {
            stream_id: False for stream_id in self.__streams__.keys()
        }

        for publisher in self.publishers.values():
            for stream_id in stream_is_published.keys():
                stream_set = set(self.__streams__[stream_id].topic_paths)
                if len(stream_set.intersection(publisher.published_topic_paths)) > 0:
                    stream_is_published[stream_id] = True

        for subscriber in self.subscribers.values():
            for stream_id in stream_is_subscribed.keys():
                if (
                    subscriber.subscribed_topic_path
                    in self.__streams__[stream_id].topic_paths
                ):
                    stream_is_subscribed[stream_id] = True

        unpublished_streams = {
            stream_id
            for stream_id, published in stream_is_published.items()
            if not published
        }
        unsubscribed_streams = {
            stream_id
            for stream_id, subscribed in stream_is_subscribed.items()
            if not subscribed
        }

        if len(unpublished_streams) > 0 or len(unsubscribed_streams) > 0:
            message = f"{self.__class__.__name__} has unused topics:\n"
            submessages = []
            if len(unpublished_streams) > 0:
                for stream_id in unpublished_streams:
                    for topic_path in self.__streams__[stream_id].topic_paths:
                        submessages.append(f"\t- {topic_path} has no publishers\n")
            if len(unsubscribed_streams) > 0:
                for stream_id in unsubscribed_streams:
                    for topic_path in self.__streams__[stream_id].topic_paths:
                        submessages.append(f"\t- {topic_path} has no subscribers\n")
            message += "".join(sorted(submessages))
            message += (
                "This could mean that there are publishers and/or subscribers of "
                "Cthulhu streams that LabGraph doesn't know about, and/or that data "
                "in some topics is being discarded.\n"
            )

            # TODO: We warn instead of raising an error because LabGraph currently
            # tries to run any publishers/subscribers it knows about as async functions,
            # so for now we keep it ignorant of C++ publisher/subcriber methods.
            logger.warning(message.strip())

    def _get_streams_by_logging_id(self) -> Dict[str, Stream]:
        logging_spec: Dict[str, Topic] = self.logging()
        return {
            logging_id: self._stream_for_topic_path(self._get_topic_path(topic))
            for logging_id, topic in logging_spec.items()
        }

    def process_modules(self) -> Sequence[Module]:
        """
        Returns a set of modules that will be the root of each process in this
        graph when it is executed in a distributed way. By default, this graph
        is the only process module, meaning the entire graph is run in a single
        process. Override this method in a graph to specify a different
        distribution of modules over processes.
        """
        return (self,)

    def logging(self) -> Dict[str, Topic]:
        """
        Returns a dictionary, where each key value pair represents a
        `Topic` to be logged.  The logger will be provided the string key as
        the identifier for the logged topic.  `HDF5Logger` (the default logger) uses
        this string identifier as the HDF5 dataset name.
        """
        return {}
