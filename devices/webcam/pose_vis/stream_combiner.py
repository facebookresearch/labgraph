import asyncio
import time
import labgraph as lg

from pose_vis.camera_stream import VideoFrame
from pose_vis.performance_tracking import PerfUtility
from typing import List, Optional
from threading import Lock
from dataclasses import dataclass, field

@dataclass
class StreamMetaData():
    updates_per_second: int
    update_time_ms: int
    frame_index: int
    device_id: int
    stream_id: int

class CombinedVideoStream(lg.Message):
    frames: List[lg.NumpyDynamicType]
    metadatas: List[StreamMetaData]
    update_time_ms: int

class VideoStreamConbinerConfig(lg.Config):
    num_devices: int
    sample_rate: int

class VideoStreamCombinerState(lg.State):
    frame_list: List[lg.NumpyDynamicType] = field(default_factory = list)
    metadata_list: List[StreamMetaData] = field(default_factory = list)
    frames_received: int = 0
    lock: Optional[Lock] = None
    last_yeild_time: int = 0

class VideoStreamCombiner(lg.Node):
    INPUT0 = lg.Topic(VideoFrame)
    INPUT1 = lg.Topic(VideoFrame)
    INPUT2 = lg.Topic(VideoFrame)
    INPUT3 = lg.Topic(VideoFrame)
    OUTPUT = lg.Topic(CombinedVideoStream)
    config: VideoStreamConbinerConfig
    state: VideoStreamCombinerState

    def setup(self) -> None:
        self.state.frame_list = [None] * self.config.num_devices
        self.state.metadata_list = [None] * self.config.num_devices
        self.state.lock = Lock()

    async def update_state(self, message: VideoFrame) -> None:
        with self.state.lock:
            self.state.frame_list[message.stream_id] = message.frame
            self.state.metadata_list[message.stream_id] = StreamMetaData(
                updates_per_second = message.updates_per_second,
                update_time_ms = message.update_time_ms,
                frame_index = message.frame_index,
                device_id = message.device_id,
                stream_id = message.stream_id)
            self.state.frames_received += 1

    @lg.subscriber(INPUT0)
    async def on_frame_received_0(self, message: VideoFrame) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT1)
    async def on_frame_received_1(self, message: VideoFrame) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT2)
    async def on_frame_received_2(self, message: VideoFrame) -> None:
        await self.update_state(message)
    
    @lg.subscriber(INPUT3)
    async def on_frame_received_3(self, message: VideoFrame) -> None:
        await self.update_state(message)

    @lg.publisher(OUTPUT)
    async def send_frames(self) -> lg.AsyncPublisher:
        while True:
            with self.state.lock:
                if self.state.frames_received >= self.config.num_devices:
                    yield self.OUTPUT, CombinedVideoStream(
                        frames = self.state.frame_list.copy(),
                        metadatas = self.state.metadata_list.copy(),
                        update_time_ms = self.state.last_yeild_time if self.state.last_yeild_time == 0 else PerfUtility.ns_to_ms(time.time_ns() - self.state.last_yeild_time))
                    self.state.frames_received = 0
                    self.state.last_yeild_time = time.time_ns()

            await asyncio.sleep(0)