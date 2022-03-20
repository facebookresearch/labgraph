#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.
import pickle
from typing import List, Tuple

import numpy as np
from imu_types_pb2 import ImuPacket
from labgraph import ProcessingHistory, RawReceivedMessage, Sample, Serializer


class IMUSerializer(Serializer):
    frame = ImuPacket()

    def serialize(self, message: List[Sample]) -> bytes:
        """
        When serializing, we pickle the Sample instead of reproducing the
        protobuf format so that we can keep the processed_timestamps information
        """
        return pickle.dumps(message)

    def deserialize(self, message: RawReceivedMessage) -> List[Sample]:
        try:
            # Try to unpickle a sample
            return pickle.loads(message.message)
        except pickle.UnpicklingError:
            # If it's not a pickled sample, it's the betazoid protobuf format
            self.frame.ParseFromString(message.message)
            timestamps, samples = self._message_to_array(self.frame)
            return Sample.from_np(
                timestamps=timestamps,
                data=samples,
                history=ProcessingHistory.received(message.received_timestamp),
            )

    def _message_to_array(self, message: ImuPacket) -> Tuple[np.ndarray, np.ndarray]:
        num_frames = len(message.frames)
        data = np.zeros((num_frames, 6))

        timestamps = np.zeros(num_frames)

        for frame_idx, frame in enumerate(message.frames):
            data[frame_idx] = np.array(
                (
                    frame.gyro_x,
                    frame.gyro_y,
                    frame.gyro_z,
                    frame.accel_x,
                    frame.accel_y,
                    frame.accel_z,
                )
            )
            timestamps[frame_idx] = frame.timestamp

        return timestamps, data
