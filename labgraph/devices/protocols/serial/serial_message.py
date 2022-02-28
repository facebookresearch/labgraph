#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from labgraph.messages import Message


class SERIALMessage(Message):
    """
    A message representing data that was/will be communicated to Serial.
    """

    data: bytes