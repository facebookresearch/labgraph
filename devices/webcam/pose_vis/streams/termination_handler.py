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
    INPUT = lg.Topic(FinishedMessage)
    config: TerminationHandlerConfig
    state: TerminationHandlerState

    def setup(self) -> None:
        self.state.lock = Lock()

    @lg.subscriber(INPUT)
    async def on_finished(self, message: FinishedMessage) -> None:
        with self.state.lock:
            self.state.num_finished += 1
    
    @lg.main
    def on_main(self) -> None:
        while True:
            with self.state.lock:
                if self.state.num_finished == self.config.num_streams:
                    break
            time.sleep(0.5)
        raise lg.NormalTermination
