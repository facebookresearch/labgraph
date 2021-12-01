#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import itertools
from typing import List

from ....util.logger import get_logger
from .ws_session import WebSocketSession

logger = get_logger(__name__)


class SessionManager:
    _sessions: List[WebSocketSession] = []
    _session_iterator = itertools.count()

    def num_sessions(self) -> int:
        return len(self._sessions)

    def add_websocket_session(self, ip: str, port: int, enums: object) -> int:
        session_id = self.get_session_id()
        session = WebSocketSession(
            session_id=session_id,
            ip=ip,
            port=port,
            enums=enums,
        )
        session.start()
        self._sessions.append(session)

        return session_id

    def get_session_id(self) -> int:
        return next(self._session_iterator)

    def get_session(self, session_id: int) -> WebSocketSession:
        return self._sessions[session_id]

    def clear_sessions(self) -> None:
        for session in self._sessions:
            session.stop()
        self._sessions = []
