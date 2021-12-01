#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
from typing import List

from ....util.logger import get_logger
from ..api.api_stream_descendant import ApiStreamDesc
from ..session.ws_server import WSServer
from ..session.ws_session import WebSocketSession


logger = get_logger(__name__)


async def send_sample_ws_message_with_active_server(
    stream_name: str,
    stream_id: str,
    wsServer: WSServer,
    session: WebSocketSession,
    sample_rate: int,
    samples: List,
):
    stream_desc = ApiStreamDesc(stream_name=stream_name, stream_id=stream_id)
    session.add_stream(stream_desc=stream_desc)

    while wsServer.isactive(stream_name):
        if stream_name in wsServer.streams:
            await session.send_samples(
                samples=samples,
                stream_name=stream_name,
            )
            await asyncio.sleep(1 / sample_rate)


async def send_sample_ws_message(
    stream_name: str,
    stream_id: str,
    wsServer: WSServer,
    session: WebSocketSession,
    sample_rate: int,
    samples: List,
):
    while wsServer is None or not wsServer.isactive(stream_name):
        await asyncio.sleep(1 / sample_rate)

    logger.info(f"Stream {stream_name} has been activated.")

    await send_sample_ws_message_with_active_server(
        stream_name=stream_name,
        stream_id=stream_id,
        wsServer=wsServer,
        session=session,
        sample_rate=sample_rate,
        samples=samples,
    )
