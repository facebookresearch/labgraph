#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import time
import asyncio
import numpy as np
import labgraph as lg

# from delsysAPI.AeroPy.TrignoBase import *  # noqa: F403
# from delsysAPI.DataCollector import CollectDataController
# # from messages.lgMessages import messageDelsys, messageUI
# from delsysAPI..AeroPy.
from .helpers.Rate import Rate
from .delsys import Delsys


# The messages for the Delsys data
class messageEMG(lg.Message):
    timestamps: np.ndarray
    data: np.ndarray


# The messages to chage the Delsys state
class messageDelsysState(lg.Message):
    timestamp: float
    setConnectState: bool
    setPairState: bool
    setScanState: bool
    setStartState: bool
    setStopState: bool


# The configuration for the Delsys
class configDelsys(lg.Config):
    sample_rate: float  # Rate at which to get data


# The state for the Delsys
class stateDelsys(lg.State):
    Connect: bool = False
    Pair: bool = False
    Scan: bool = False
    Start: bool = False
    Stop: bool = False
    Ready: bool = False


# ================================= DELSYS DATA PUBLISHER ====================================
# A data source node that generates random noise to a single output topic
class nodeDelsys(lg.Node):
    INPUT = lg.Topic(messageDelsysState)
    OUTPUT = lg.Topic(messageEMG)
    config: configDelsys
    state: stateDelsys

    def setup(self) -> None:
        self.Delsys = Delsys()
        self.rate = Rate(self.config.sample_rate)
        self.shutdown = False

    def cleanup(self) -> None:
        self.shutdown = True

    def setDelsysState(self) -> None:
        if self.state.Connect:
            self.Delsys.connect()
            self.state.Connect = False
        elif self.state.Pair:
            self.Delsys.pair()
            self.state.Pair = False
        elif self.state.Scan:
            self.Delsys.scan()
            self.state.Scan = False
        elif self.state.Start:
            self.Delsys.start()
            self.state.Start = False
            self.state.Ready = True
        elif self.state.Stop:
            self.Delsys.stop()
            self.state.Stop = False
            self.state.Ready = False

    # A subscriber method that simply receives data and updates the node's state
    @lg.subscriber(INPUT)
    def getDelsysState(self, message: messageDelsysState) -> None:
        self.state.Connect = message.setConnectState
        self.state.Pair = message.setConnectState
        self.state.Scan = message.setScanState
        self.state.Start = message.setStartState
        self.state.Stop = message.setStopState
        self.setDelsysState()

    # A publisher method that produces data on a single topic
    @lg.publisher(OUTPUT)
    async def publishEMG(self) -> lg.AsyncPublisher:

        isFirstData = True
        while not self.shutdown:
            if self.state.Ready:
                EMGData = self.Delsys.getEMGData()
                if isFirstData and (EMGData is not None):
                    isFirstData = False
                    self.rate.last_time = time.time()
                if EMGData is not None:
                    timestampArray = np.linspace(self.rate.last_time, self.rate.last_time + self.rate.sleep_dur, num=EMGData.shape[1], endpoint=False)
                    yield self.OUTPUT, messageEMG(timestamps=timestampArray, data=EMGData)
                    await self.rate.sleep()
            await asyncio.sleep(0)
# ================================= DELSYS DATA PUBLISHER ===================================
