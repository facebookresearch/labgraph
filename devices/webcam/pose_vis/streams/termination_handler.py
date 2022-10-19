import time
import labgraph as lg

from pose_vis.streams.messages import FinishedMessage
from typing import Optional
from threading import Lock

class TerminationHandlerConfig(lg.Config):
    """
    Config for TerminationHandler

    Attributes:
        `num_streams`: `int`
    """
    num_streams: int

class TerminationHandlerState(lg.State):
    """
    State for TerminationHandler

    Attributes:
        `num_finished`: `int`
    """
    num_finished: int
    lock: Optional[Lock] = None
    

class TerminationHandler(lg.Node):
    """
    Waits until number of `FinishedMessage`s received matches `num_streams` and then terminates the graph

    Topics:
        `INPUT`: `FinishedMessage`
    
    Attributes:
        `config`: `TerminationHandlerConfig`
        `state`: `TerminationHandlerState`
    """
    INPUT0 = lg.Topic(FinishedMessage)
    INPUT1 = lg.Topic(FinishedMessage)
    INPUT2 = lg.Topic(FinishedMessage)
    INPUT3 = lg.Topic(FinishedMessage)
    config: TerminationHandlerConfig
    state: TerminationHandlerState

    def setup(self) -> None:
        self.state.lock = Lock()

    async def update_state(self, message: FinishedMessage) -> None:
        with self.state.lock:
            self.state.num_finished += 1
    
    @lg.subscriber(INPUT0)
    async def on_finished_0(self, message: FinishedMessage) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT1)
    async def on_finished_1(self, message: FinishedMessage) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT2)
    async def on_finished_2(self, message: FinishedMessage) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT3)
    async def on_finished_3(self, message: FinishedMessage) -> None:
        await self.update_state(message)
    
    @lg.main
    def on_main(self) -> None:
        while True:
            with self.state.lock:
                if self.state.num_finished == self.config.num_streams:
                    break
            time.sleep(0.5)
        raise lg.NormalTermination
