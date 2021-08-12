#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import asyncio
from typing import Dict, List

import importlib_resources
import labgraph as lg
from psychopy import monitors, visual


class KeysMessage(lg.Message):
    keys: List[str]


class DisplayMessage(lg.Message):
    key: str


class Controller(lg.Node):
    """
    This node controls the flow of the experiment, i.e., deciding the order in which
    to trigger display changes.

    This is a contrived example that receives the set of keys from the display node,
    and then iterates over them in a round robin fashion to trigger display changes.
    """
    KEYS_TOPIC = lg.Topic(KeysMessage)
    DISPLAY_TOPIC = lg.Topic(DisplayMessage)

    def setup(self) -> None:
        self._keys = None

    @lg.subscriber(KEYS_TOPIC)
    def set_keys(self, message: KeysMessage) -> None:
        """
        This function subscribes to the specified topic that receives the list of known
        display keys after setting up the psychopy stims for them.

        When a message is received, it sets the internal variable, which unblocks the
        main control publisher loop.
        """
        self._keys = message.keys

    @lg.publisher(DISPLAY_TOPIC)
    async def control(self) -> lg.AsyncPublisher:
        """
        This function waits until keys is set (this is when the display node is ready)
        then loops for a finite time, publishing the "next" key on the specified topic.

        Once the loop is exhausted, the node raises a NormalTermination, which signals
        to the rest of the graph to cleanup and shutdown.
        """
        while self._keys is None:
            await asyncio.sleep(0.1)
        for i in range(10):
            key = self._keys[i % len(self._keys)]
            yield (self.DISPLAY_TOPIC, DisplayMessage(key))
            await asyncio.sleep(1.0)
        raise lg.NormalTermination()


class Display(lg.Node):
    """
    This node sets up psychopy stims, signals when it is ready and changes displayed
    stims according to events received on the specified topic.
    """
    KEYS_TOPIC = lg.Topic(KeysMessage)
    DISPLAY_TOPIC = lg.Topic(DisplayMessage)

    def setup(self) -> None:
        self._stims = None
        self._shutdown = False

    def cleanup(self) -> None:
        """
        This function is called when a NormalTermination is raised, so we set relevant
        shutdown flags here. We can use this to break out of infinite loops.
        """
        self._shutdown = True

    def _setup_stims(self, window: visual.Window) -> Dict[str, visual.BaseVisualStim]:
        """
        Setup the dictionary of key -> stim for this node.

        This cannot be done in the `setup` function because the window needs to be
        available, and psychopy needs the window to be created in the "main" thread.
        """
        files = importlib_resources.files("psychopy_example")
        null = files / "images" / "null.png"
        with importlib_resources.as_file(null) as null_path:
            image_stim = visual.ImageStim(window, image=str(null_path), pos=(0, 0))
        text_stim = visual.TextStim(window, text="Example Text", pos=(0, 0))
        self._stims = {
            "image": image_stim,
            "text": text_stim,
        }

    @lg.publisher(KEYS_TOPIC)
    async def send_keys(self) -> lg.AsyncPublisher:
        """
        This function waits until stims is set, publishes the list of keys
        on the specified topic and then stops running.
        """
        while self._stims is None:
            await asyncio.sleep(0.1)
        yield(self.KEYS_TOPIC, KeysMessage(list(self._stims.keys())))

    @lg.subscriber(DISPLAY_TOPIC)
    def update_stim(self, message: DisplayMessage) -> None:
        """
        This function subscribes to the specified topic that receives the "next" key
        and updates the `autoDraw` status of all known stims.
        """
        for stim in self._stims.values():
            stim.autoDraw = False
        self._stims[message.key].autoDraw = True

    @lg.main
    def display(self):
        """
        This function runs in the main thread and sets up required psychopy objects.

        After initial setup is done, it loops until signaled to shutdown, and flips
        the psychopy frame. At every frame flip, the stims with `autoDraw` set to True
        are displayed.
        - Note that frame flips are inherently throttled by screen refresh rates, so
          this is not a tight loop and does not need to manually sleep between flips.
        """
        monitor = monitors.Monitor("PsychopyMonitor")
        window = visual.Window(fullscr=True)
        self._setup_stims(window)
        while not self._shutdown:
            window.flip()
        window.close()
