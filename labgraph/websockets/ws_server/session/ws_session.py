#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
from threading import Thread

import websockets

from ....util.logger import get_logger
from .session import Session
from .ws_server import WSServer

logger = get_logger(__name__)


class WebSocketSession(Session):
    def __init__(self, ip: str, port: int, session_id: int, enums: object):
        super().__init__(
            session_id=session_id,
            enums=enums,
        )
        self.ip = ip
        self.port = port

    def start(self) -> None:
        self.wsServer = WSServer(enums=self.enums)
        start_server = websockets.serve(self.wsServer.process, self.ip, self.port)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(start_server)
        self.thread = Thread(target=self.loop.run_forever)

        self.thread.start()

        logger.info("WebSocketSession Started!")

    def stop(self) -> None:
        self.loop.call_soon_threadsafe(self.loop.stop)
        logger.info("WebSocketSession Stop Requested!")
        self.thread.join()
        logger.info("WebSocketSession Stop Completed!")

    async def write(self, data: str, sleep_time: float = 0.001) -> bool:
        # await self.wsServer.send_samples(data)
        # await asyncio.sleep(sleep_time)
        write_success = True
        try:
            await self.wsServer.send_samples(data)
            write_success = True
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(e)
            write_success = False

        await asyncio.sleep(sleep_time)
        return write_success
