#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
from typing import List

import labgraph as lg
from psychopy import monitors, visual


class KeysMessage(lg.Message):
    keys: List[str]


class DisplayMessage(lg.Message):
    key: str


class Controller(lg.Node):
    KEYS_TOPIC = lg.Topic(KeysMessage)
    DISPLAY_TOPIC = lg.Topic(DisplayMessage)

    def setup(self) -> None:
        self._keys = None

    @lg.subscriber(KEYS_TOPIC)
    def set_keys(self, message: KeysMessage) -> None:
        self._keys = message.keys

    @lg.publisher(DISPLAY_TOPIC)
    def control(self) -> lg.AsyncPublisher:
        while self._keys is None:
            asyncio.sleep(0.1)
        for i in range(10):
            key = self._keys[i % len(self._keys)]
            yield (DISPLAY_TOPIC, DisplayMessage(key))
            asyncio.sleep(5.0)
        raise lg.NormalTermination()


class Display(lg.Node):
    KEYS_TOPIC = lg.Topic(KeysMessage)
    DISPLAY_TOPIC = lg.Topic(DisplayMessage)

    def setup(self) -> None:
        self._stims = None
        self._shutdown = False

    def cleanup(self) -> None:
        self._shutdown = True

    def _setup_stims(self, window: visual.Window) -> Dict[str, visual.BaseVisualStim]:
        image_stim = visual.ImageStim(window, image="images/null.png", pos=(0, 0))
        text_stim = visual.TextStim(window, text="Example Text", pos=(0, 0))
        self._stims = {
            "image": image_stim,
            "text": text_stim,
        }

    @lg.publisher(KEYS_TOPIC)
        while self._stims is None:
            asyncio.sleep(0.1)
        yield(self.KEYS_TOPIC, KeysMessage(list(self._stims.keys())))

    @lg.subscriber(DISPLAY_TOPIC)
    def update_stim(self, message: DisplayMessage) -> None:
        for stim in self._stims.values():
            stim.autoDraw = False
        self._stims[message.key].autoDraw = True

    @lg.main
    def display(self):
        monitor = monitors.Monitor("PsychopyMonitor")
        window = visual.Window(fullscr=True)
        self._setup_stims(window)
        while not self._shutdown:
            window.flip()
        window.close()
