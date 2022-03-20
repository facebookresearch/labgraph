#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time
from typing import List

import yaml
from labgraph import Node

SLEEP_TIME = 1.0


class YamlNode(Node):
    """
    YamlNode
    Reads a yaml file and publishes the contents to a topic
    """

    def __init__(self, name: str, yaml_path: str, output_topic: str) -> None:
        """
        Initialize a YamlNode

        Args:
            name: The name of the node
            yaml_path: Path to a yaml file to read
            output_topic: topic to publish yaml file contents to
        """
        super(YamlNode, self).__init__(name)
        self.yaml_path = yaml_path
        self.output_topic = output_topic

    def subscribe_topics(self) -> List[str]:
        return []

    def publish_topics(self) -> List[str]:
        return [self.output_topic]

    def main(self) -> None:
        with open(self.yaml_path) as file:
            self.publish(self.output_topic, yaml.load(file, Loader=yaml.FullLoader))

        # HACK: Prevent the node from shutting down and flushing its channels
        # The channel flush could cause the yaml data not to be written to disk
        time.sleep(SLEEP_TIME)
