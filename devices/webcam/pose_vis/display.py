import asyncio
from multiprocessing.sharedctypes import synchronized
from turtle import st
import cv2
import time
import labgraph as lg
import numpy as np

from typing import List, Optional
from dataclasses import field
from threading import Lock
from pose_vis.performance_tracking import PerfUtility
from pose_vis.camera_stream import ReadyMessage
from pose_vis.stream_combiner import CombinedVideoStream, StreamMetaData
from pose_vis.extension import ExtensionResult

class DisplayState(lg.State):
    frames: List[lg.NumpyDynamicType] = field(default_factory = list)
    metadatas: List[StreamMetaData] = field(default_factory = list)
    result_frames: List[Optional[List[lg.NumpyDynamicType]]] = field(default_factory = list)
    extension_perf: List[float] = field(default_factory = list)
    lock: Optional[Lock] = None
    perf: PerfUtility = PerfUtility()
    got_frames: bool = False
    extension_messages_received: int = 0
    combiner_update_time_ms: int = 0
    last_synchonization_time: int = 0
    window_open: bool = False
    window_title: str = "Pose Vis (stream {}, device {})"

class DisplayConfig(lg.Config):
    sample_rate: int
    num_extensions: int
    synchronized: bool

class Display(lg.Node):
    INPUT = lg.Topic(CombinedVideoStream)
    OUTPUT = lg.Topic(ReadyMessage)
    EXTENSION_INPUT0 = lg.Topic(ExtensionResult)
    EXTENSION_INPUT1 = lg.Topic(ExtensionResult)
    EXTENSION_INPUT2 = lg.Topic(ExtensionResult)
    EXTENSION_INPUT3 = lg.Topic(ExtensionResult)
    state: DisplayState
    config: DisplayConfig

    @lg.subscriber(INPUT)
    async def got_frame(self, message: CombinedVideoStream) -> None:
        with self.state.lock:
            self.state.frames = message.frames
            self.state.metadatas = message.metadatas
            self.state.combiner_update_time_ms = message.update_time_ms
            self.state.got_frames = True
    
    async def update_extension_results(self, message: ExtensionResult) -> None:
        with self.state.lock:
            self.state.result_frames[message.extension_id] = message.result_frames
            self.state.extension_perf[message.extension_id] = message.update_time_ms
            self.state.extension_messages_received += 1

    @lg.subscriber(EXTENSION_INPUT0)
    async def on_extension_received_0(self, message: ExtensionResult) -> None:
        await self.update_extension_results(message)
    
    @lg.subscriber(EXTENSION_INPUT1)
    async def on_extension_received_1(self, message: ExtensionResult) -> None:
        await self.update_extension_results(message)

    @lg.subscriber(EXTENSION_INPUT2)
    async def on_extension_received_2(self, message: ExtensionResult) -> None:
        await self.update_extension_results(message)

    @lg.subscriber(EXTENSION_INPUT3)
    async def on_extension_received_3(self, message: ExtensionResult) -> None:
        await self.update_extension_results(message)

    def setup(self) -> None:
        self.state.result_frames = [None] * self.config.num_extensions
        self.state.extension_perf = [0] * self.config.num_extensions
        self.state.lock = Lock()

    @lg.publisher(OUTPUT)
    async def display(self) -> lg.AsyncPublisher:
        perf = PerfUtility()

        yield self.OUTPUT, ReadyMessage()

        while True:
            perf.update_start()
            start_time_ns = time.time_ns()

            with self.state.lock:
                if not self.config.synchronized or (self.state.got_frames and self.state.extension_messages_received == self.config.num_extensions):
                    for i in range(len(self.state.frames)):
                        title = self.state.window_title.format(i, self.state.metadatas[i].device_id)

                        frame = self.state.frames[i]

                        for e in range(self.config.num_extensions):
                            frame = cv2.addWeighted(self.state.result_frames[e][i], 0.5, frame, 0.5, 0.5)

                        cv2.imshow(title, frame)
                        self.state.window_open = True

                    yield self.OUTPUT, ReadyMessage()
                    self.state.got_frames = False
                    self.state.extension_messages_received = 0
                    self.state.last_synchonization_time = time.time_ns()
                    
                if self.state.window_open:
                    for i in range(len(self.state.metadatas)):
                        title = self.state.window_title.format(i, self.state.metadatas[i].device_id)
                        cv2.setWindowTitle(title, f"{title}, {perf.updates_per_second} FPS (syncronization: {PerfUtility.ns_to_ms(time.time_ns() - self.state.last_synchonization_time):03d}ms), Combiner: {self.state.combiner_update_time_ms:03d}ms, Stream: {self.state.metadatas[i].updates_per_second} FPS: {self.state.metadatas[i].update_time_ms:03d}ms, Extension timings: {self.state.extension_perf}ms")

            if cv2.waitKey(1) & 0xFF == 27:
                break

            wait_time_ns = perf.get_sleep_time_ns(start_time_ns, self.config.sample_rate)
            await asyncio.sleep(PerfUtility.ns_to_s(wait_time_ns))

            perf.update_end()
        
        cv2.destroyAllWindows()
        raise lg.NormalTermination()