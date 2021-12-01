#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import json
from typing import Any, Tuple

import websockets

from ....util.logger import get_logger
from ..api.api_request import APIRequest
from ..api.ws_api_message_constructor import (
    get_start_stream_request,
    get_end_stream_request,
    get_start_stream_request_error,
)


# TODO: refactor logger to LOGGER.
logger = get_logger(__name__)


class WSServer:
    def __init__(
        self,
        enums: Any,
        request_time_out=0.01,
        sleep_pause_time=0.1,
    ):
        self.enums = enums

        self.STREAM_LISTS = getattr(enums, "STREAM_LISTS", set())
        self.supported_stream_list = getattr(
            self.STREAM_LISTS, "supported_stream_list", set()
        )
        self.sleep_pause_streams = getattr(
            self.STREAM_LISTS, "sleep_pause_streams", set()
        )

        self.streams = {}
        self.stream_id_to_stream_name = {}
        self.request_time_out = request_time_out
        self.sleep_pause_time = sleep_pause_time
        self.websocket = None
        self.states = None

    def isactive(self, stream_name) -> bool:
        return stream_name in self.streams

    def remove_stream(self, stream_name) -> None:
        if stream_name in self.streams:
            del self.streams[stream_name]

    async def end_stream_listener(self) -> bool:
        """Coroutine for receiving and parsing incoming stream messages
        asynchronously."""
        request = None
        while not request or request.is_start_stream_request():
            try:
                request = APIRequest(
                    await asyncio.wait_for(
                        self.websocket.recv(), timeout=self.request_time_out
                    ),
                    enums=self.enums,
                )
            except asyncio.TimeoutError:
                # Normal timeout
                break
        return request.is_end_stream_request() if request else False

    async def send_samples(self, msg) -> None:
        await self.websocket.send(msg)

    async def start_connection(self, request) -> None:
        start_stream_request_msg = get_start_stream_request(
            stream_id=request.stream_id,
            request_id=request.request_id,
            api_version=self.enums.WS_SERVER.DEFAULT_API_VERSION,
        )
        await self.websocket.send(json.dumps(start_stream_request_msg))
        self.streams[request.stream_name] = request
        self.stream_id_to_stream_name[request.stream_id] = request.stream_name

    async def start_connection_error(self, request) -> None:
        start_stream_request_msg = get_start_stream_request_error(
            stream_id=request.stream_id,
            request_id=request.request_id,
            api_version=self.enums.WS_SERVER.DEFAULT_API_VERSION,
        )
        await self.websocket.send(json.dumps(start_stream_request_msg))
        self.streams[request.stream_name] = request
        self.stream_id_to_stream_name[request.stream_id] = request.stream_name

    async def ws_recv(self) -> Tuple[str, bool]:
        recv_success = False
        try:
            msg = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=self.request_time_out,
            )
            recv_success = True
        except asyncio.TimeoutError:
            # Normal timeout
            msg = ""
        except websockets.exceptions.ConnectionClosedError:
            # Connection from Client is closed/interrupted
            msg = ""

        return msg, recv_success

    def is_start_stream_request(self, msg: str) -> bool:
        return self.enums.API.START_STREAM_REQUEST in msg

    def is_end_stream_request(self, msg: str) -> bool:
        return self.enums.API.END_STREAM_REQUEST in msg

    async def process(self, websocket, path) -> None:
        """
        Main Process for handling websocket process.
        """
        logger.info("Start of WebSocket Process...")
        self.websocket = websocket

        while True:
            msg, recv_success = await self.ws_recv()

            if self.is_start_stream_request(msg):
                request = APIRequest(
                    msg,
                    enums=self.enums,
                )
                stream_name = request.stream_name
                stream_id = request.stream_id

                if not self.isactive(stream_name):
                    if (
                        self.supported_stream_list is None
                        or stream_name in self.supported_stream_list
                    ):
                        await self.start_connection(request)
                        logger.info(f"Connected to stream {stream_name}")
                    else:
                        await self.start_connection_error(request)
                        logger.info(
                            f"Stream {stream_name} is not in supported_stream_list."
                        )

                    self.streams[stream_name] = request
                    self.stream_id_to_stream_name[stream_id] = stream_name

            elif self.is_end_stream_request(msg):
                request = APIRequest(
                    msg,
                    enums=self.enums,
                )
                stream_name = self.stream_id_to_stream_name[request.stream_id]

                if self.isactive(stream_name):
                    del self.streams[stream_name]
                    del self.stream_id_to_stream_name[request.stream_id]
                    end_stream_request_msg = get_end_stream_request(
                        stream_id=request.stream_id,
                        request_id=request.request_id,
                        api_version=self.enums.WS_SERVER.DEFAULT_API_VERSION,
                    )
                    await websocket.send(json.dumps(end_stream_request_msg))
                    logger.info(f"Stream {stream_name} has been closed.")

            for sleep_pause_stream in self.sleep_pause_streams:
                if sleep_pause_stream in msg or not recv_success:
                    await asyncio.sleep(self.sleep_pause_time)
