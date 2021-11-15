#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
from threading import Thread

import websockets

from ...tests.enums import WS_SERVER, ENUMS
from ..session_manager import SessionManager
from ..ws_server import WSServer
from ..ws_session import WebSocketSession


class TestWSServerSession:
    def test_session_manager(self) -> None:
        session_manager = SessionManager()
        ip = WS_SERVER.DEFAULT_IP
        port = WS_SERVER.DEFAULT_PORT
        session_manager.add_websocket_session(
            ip=ip,
            port=port,
            enums=ENUMS(),
        )
        session_manager.clear_sessions()

    def test_ws_session(self) -> None:
        ip = WS_SERVER.DEFAULT_IP
        port = WS_SERVER.DEFAULT_PORT + 1

        session = WebSocketSession(
            session_id=0,
            ip=ip,
            port=port,
            enums=ENUMS(),
        )
        session.start()
        session.stop()

    def test_ws_server(self) -> None:
        wsServer = WSServer(enums=ENUMS())

        ip = WS_SERVER.DEFAULT_IP
        port = WS_SERVER.DEFAULT_PORT + 2

        start_server = websockets.serve(wsServer.process, ip, port)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_server)
        thread = Thread(target=loop.run_forever)

        thread.start()
        loop.call_soon_threadsafe(loop.stop)
        thread.join()
