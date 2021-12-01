#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import time
from typing import List

from ...graphs import Config, Node
from ...graphs.method import main
from ...util.logger import get_logger
from .session.session_manager import SessionManager


logger = get_logger(__name__)


class WSServerConfig(Config):
    app_id: str
    ip: str
    port: int
    api_version: str
    enums: object


class WSServerNode(Node):
    """
    Represents a node in the graph which serves as a WebSocket server.

    Args:
        client: The websocket client which handles websocket request.
    """

    config: WSServerConfig

    @main
    def main_loop(self) -> None:
        logger.info("Start of main_loop")
        session_manager = SessionManager()
        session_id = session_manager.add_websocket_session(
            ip=self._ip,
            port=self._port,
            enums=self.enums,
        )
        logger.info(f"WebSocket Session {session_id} Added and Started.")

        self.session = session_manager.get_session(session_id)
        self.wsServer = self.session.wsServer

        while not self.shutdown:
            time.sleep(0.1)
        session_manager.clear_sessions()
        logger.info("WSServerNode Closed Normally.")

    def setup(self) -> None:
        logger.info("WSServerNode Setting Up.")
        self._ip = self.config.ip
        self._port = self.config.port
        self.app_id = self.config.app_id
        self.api_version = self.config.api_version
        self.enums = self.config.enums

        self.stream: List = []

        self.shutdown = False

    def cleanup(self) -> None:
        logger.info("WSServerNode Cleaning Up.")
        self.shutdown = True
