import time
import labgraph as lg

from pose_vis.streams.messages import ExitSignal

class TerminationHandlerState(lg.State):
    """
    State for TerminationHandler

    Attributes:
        `signal_received`: `bool`
    """
    signal_received: bool = False

class TerminationHandler(lg.Node):
    """
    Terminates the graph cleanly upon receiving `ExitSignal`

    Topics:
        `INPUT`: `ExitSignal`
    
    Attributes:
        `state`: `TerminationHandlerState`
    """
    INPUT_EXIT_STREAM = lg.Topic(ExitSignal)
    INPUT_EXIT_USER = lg.Topic(ExitSignal)
    state: TerminationHandlerState

    @lg.subscriber(INPUT_EXIT_STREAM)
    async def on_exit_stream(self, _: ExitSignal) -> None:
        self.state.signal_received = True
    
    @lg.subscriber(INPUT_EXIT_USER)
    async def on_exit_user(self, _: ExitSignal) -> None:
        self.state.signal_received = True
    
    @lg.main
    def on_main(self) -> None:
        while True:
            if self.state.signal_received:
                break
            time.sleep(0.1)
        raise lg.NormalTermination
