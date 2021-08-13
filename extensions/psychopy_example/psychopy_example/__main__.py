#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Dict, Sequence

import labgraph as lg

from .components import Controller, Display

class PsychopyExample(lg.Graph):
    CONTROLLER: Controller
    DISPLAY: Display

    def process_modules(self) -> Sequence[lg.Module]:
        return (self.CONTROLLER, self.DISPLAY)

    def connections(self) -> lg.Connections:
        return (
            (self.CONTROLLER.DISPLAY_TOPIC, self.DISPLAY.DISPLAY_TOPIC),
            (self.DISPLAY.KEYS_TOPIC, self.CONTROLLER.KEYS_TOPIC),
        )

    def logging(self) -> Dict[str, lg.Topic]:
        return {"changes": self.CONTROLLER.DISPLAY_TOPIC}


if __name__ == "__main__":
    lg.run(PsychopyExample)
