#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import json
from abc import abstractmethod
from collections import defaultdict
from typing import List, Dict, DefaultDict

from ....util.logger import get_logger
from ..api.api_stream_descendant import ApiStreamDesc

logger = get_logger(__name__)


class Session:
    session_id: int
    _active: bool
    _stream_id_to_stream_desc: Dict
    _stream_id_to_batch_num: DefaultDict

    def __init__(self, session_id: int, enums: object):
        self.session_id = session_id
        self.enums = enums
        self._active = True
        self._stream_id_to_batch_num = defaultdict(int)
        self._stream_id_to_stream_desc = {}

    async def send_samples(self, samples: List, stream_name: str) -> bool:
        send_samples_success = False
        if self._active:
            stream_descs = self.get_streams(stream_name)
            send_samples_success = True

            for stream_desc in stream_descs:
                if samples is not None:
                    message = {
                        "stream_batch": {
                            "stream_id": stream_desc.stream_id,
                            stream_name: {
                                "samples": samples,
                                "batch_num": self.increment_and_get_batch_num(
                                    stream_desc.stream_id
                                ),
                            },
                        }
                    }
                    message = json.dumps(message)
                    write_success = await self.write(data=message)
                    if not write_success:
                        self.remove_stream(stream_desc)
                        # await asyncio.sleep(sleep_time)
                        send_samples_success = False
        return send_samples_success

    @abstractmethod
    async def write(self, data: str) -> bool:
        raise NotImplementedError()

    def get_streams(self, stream_name: str) -> List[ApiStreamDesc]:
        matching_stream_descs = []
        for _stream_desc in self._stream_id_to_stream_desc.values():
            if _stream_desc.stream_name == stream_name:
                matching_stream_descs.append(_stream_desc)
        return matching_stream_descs

    def increment_and_get_batch_num(self, stream_id: str) -> int:
        self._stream_id_to_batch_num[stream_id] += 1
        return self._stream_id_to_batch_num[stream_id]

    def is_active(self) -> bool:
        return self._active

    def is_stream_name_active(self, stream_name: str) -> bool:
        for _stream_desc in self._stream_id_to_stream_desc.values():
            if _stream_desc.stream_name == stream_name:
                return True
        return False

    def get_stream_name(self, stream_name: str) -> ApiStreamDesc:
        for _stream_id, _stream_desc in self._stream_id_to_stream_desc.items():
            if _stream_desc.stream_name == stream_name:
                return _stream_desc
        return None

    def add_stream(self, stream_desc: ApiStreamDesc) -> None:
        stream_id = stream_desc.stream_id
        self._stream_id_to_stream_desc[stream_id] = stream_desc

    def remove_stream(self, stream_desc: ApiStreamDesc) -> bool:
        stream_id = stream_desc.stream_id
        if stream_id in self._stream_id_to_stream_desc.keys():
            del self._stream_id_to_stream_desc[stream_id]
            del self._stream_id_to_batch_num[stream_id]
            return True
        return False
