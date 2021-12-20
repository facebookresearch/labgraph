#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
import importlib
import time
import typing

import labgraph as lg
from labgraph_protocol.protocol import ReadyMessage, Trial
from labgraph_protocol.protocol_node import (
    CurrentTrialMessage,
    EndTrialMessage,
)
from labgraph_protocol.qt_stimulus import QtStimulus
from labgraph_protocol.qt_widgets import MainWindow
from PyQt5 import QtCore, QtWidgets


class _FullScreen:
    def __eq__(self, other: typing.Any) -> bool:
        return isinstance(other, type(self))


FULLSCREEN = _FullScreen()
PUBLISH_LOOP_TIME = 0.001
WINDOW_SIZE_T = typing.Union[typing.Tuple[int, int], _FullScreen]


class QtNodeConfig(lg.Config):
    module: str
    window_size: WINDOW_SIZE_T = (640, 480)


class QtNodeState(lg.State):
    app: typing.Optional[QtWidgets.QApplication] = None
    keypress_callbacks: typing.Optional[
        typing.Dict[int, typing.Callable[..., typing.Any]]
    ] = None
    view: typing.Optional[MainWindow] = None
    current_trial: typing.Optional[Trial] = None
    current_trial_started: bool = False
    shutdown: bool = False


class QtNode(lg.Node):
    config: QtNodeConfig
    state: QtNodeState

    CURRENT_TRIAL_TOPIC = lg.Topic(CurrentTrialMessage)
    END_TRIAL_TOPIC = lg.Topic(EndTrialMessage)
    READY_TOPIC = lg.Topic(ReadyMessage)

    def setup(self) -> None:
        # Need this import to ensure conditions are setup
        module = importlib.import_module(self.config.module)
        self.state.keypress_callbacks = {}
        self.state.keypress_callbacks.update(getattr(module, "keypress_callbacks", {}))

    @lg.main
    def run(self) -> None:
        self.state.app = QtWidgets.QApplication([])
        self.state.app.setStyle("Macintosh")
        self.state.view = MainWindow(self.state.keypress_callbacks)
        if self.config.window_size == FULLSCREEN:
            self.state.view.showFullScreen()
        else:
            self.state.view.resize(*self.config.window_size)
        scene = QtWidgets.QGraphicsScene()
        rect = self.state.view.rect()
        scene.setSceneRect(rect.x(), rect.y(), rect.width(), rect.height())
        self.state.view.setScene(scene)
        self.state.view.show()
        timer = QtCore.QTimer()
        timer.setInterval(1)  # Timeout is in ms
        timer.timeout.connect(self._update)
        timer.start()
        self.state.app.exec_()

    @lg.subscriber(CURRENT_TRIAL_TOPIC)
    def current_trial(self, message: CurrentTrialMessage) -> None:
        self.state.current_trial = message.trial

    @lg.publisher(READY_TOPIC)
    async def ready(self) -> lg.AsyncPublisher:
        while not self.state.shutdown:
            if self.state.app is None:
                await asyncio.sleep(PUBLISH_LOOP_TIME)
            else:
                yield (self.READY_TOPIC, ReadyMessage(ready=True))
                break

    @lg.publisher(END_TRIAL_TOPIC)
    async def end_trial(self) -> lg.AsyncPublisher:
        while not self.state.shutdown:
            if self.state.current_trial is None:
                await asyncio.sleep(PUBLISH_LOOP_TIME)
                continue
            completed = True
            for stimulus in self.state.current_trial.stimuli:
                if not isinstance(stimulus, QtStimulus):
                    continue
                completed = completed and stimulus.completed
            if completed:
                yield (
                    self.END_TRIAL_TOPIC,
                    EndTrialMessage(
                        timestamp=time.time(),
                        trial=self.state.current_trial,
                        reason="All stimuli completed",
                    ),
                )
                self.state.current_trial = None
                self.state.current_trial_started = False
            await asyncio.sleep(PUBLISH_LOOP_TIME)

    def cleanup(self) -> None:
        self.state.shutdown = True
        if self.state.app is not None:
            self.state.app.quit()

    def _update(self) -> None:
        if self.state.current_trial is None:
            return
        if self.state.current_trial_started:
            return
        self.state.current_trial_started = True
        for stimulus in self.state.current_trial.stimuli:
            if not isinstance(stimulus, QtStimulus):
                continue
            stimulus.start(self.state.view)
