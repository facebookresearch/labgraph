#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Callable, Union, List, Tuple

import h5py
import numpy as np

from ..data_view.array_utils import Index, scalars_to_slice_indexer
from .channel_info import ChannelInfo, StringChannelInfo


def is_valid_timestamps(timestamps: np.ndarray) -> bool:
    try:
        length = len(timestamps)
    except TypeError:
        length = 0
    if length == 1:
        return True
    if not timestamps.ndim == 1:
        return False
    return np.all(np.diff(timestamps) > 0)


def check_timestamps_and_data(timestamps: np.ndarray, data: np.ndarray) -> bool:
    if not is_valid_timestamps(timestamps):
        print("timestamps needs to be 1D, flat and monotonically increasing")
        return False

    if data.ndim != 2:
        print("data needs to be a 2D array")
        return False

    if len(timestamps) != len(data):
        print("timestamps and data need the same number of samples")
        return False

    return True


def match_data_shape_to_timestamps(
    timestamps: np.ndarray, data: np.ndarray
) -> np.ndarray:
    """
    Assume `timestamps` come from a column vector, and `data` come from
    a [time, channels] array.

    Sliced `data` can lose dimension information -- restore it here to match
    the time points
    """
    if not is_valid_timestamps(timestamps):
        print("timestamps need to be 1D, monotonically increasing")

    time_points = len(timestamps)
    if data.size < time_points:
        raise ValueError("Impossible to match data with timestamps")
    if len(data) == time_points:
        return data
    return data.reshape((time_points, -1))


class HardwareMetadata(object):
    """
    Represents the hardware specification for a given recording.
    """
    pass


class TimeSeries(object):
    """
    TimeSeries represents time series data (duh), with core properties
    `TimeSeries.timestamps` and `TimeSeries.channel_data`.

    A useful model is to think about this object as a 2D array, with
    rows increasing in time. The first column is the `timestamps`, and the
    other columns are different channels. This representation can be accessed
    through the `TimeSeries.time_series` property/method.

    `TimeSeries` enforces the invariant that time must increase monotonically,
    and the timestamps and channel_data must have the same number of time points.
    Setting either `timestamps` or `channel_data` property that violates this
    will result in errors.

    `TimeSeries` supports setting and selecting data for given time
    points (`select_time`), channels (`select_channels`), or combination of
    both (`select_channel_data_at_time`), with syntax similar to
    numpy array basic indexing.
    (https://numpy.org/doc/stable/user/basics.indexing.html#basics-indexing)

    Slicing syntax can be achieved with the help of `array_utils.SliceMaker` class.

    Specifically, `select_time` can be thought of as selecting rows,
    `select_channels` can be thought of as seleting columns of the `channel_data`,
    therefore 1D numpy array indexing applies.

    Functions can be applied to `channel_data` (`transform_channel_data`), the returned
    type (`TimeSeries` or numpy array) will differ depending on the type of transformation.
    """

    _timestamps: np.ndarray
    _channel_data: np.ndarray

    def __init__(self, timestamps: np.ndarray, channel_data: np.ndarray) -> None:
        """
        timestamps: 1D array with length equal to time
        channel_data: 2D array of shape [time, channels]
        """
        # In case we have a single number here
        timestamps = np.atleast_1d(timestamps)
        channel_data = np.atleast_1d(channel_data)
        if check_timestamps_and_data(timestamps, channel_data):
            self._timestamps = timestamps
            self._channel_data = channel_data
        else:
            raise ValueError("timestamps and channel_data not compatible")

    def __repr__(self):
        return "Time | Channels...\n" + str(self.time_series)

    def __len__(self):
        return self.shape[0]

    def __eq__(self, other: "TimeSeries") -> bool:
        return np.array_equal(self.timestamps, other.timestamps) and np.array_equal(
            self.channel_data, other.channel_data
        )

    def __getitem__(self, indexer: Tuple[Index, Index]) -> "TimeSeries":
        """
        Return new TimeSeries with given time and channel selection. Syntax is the same
        as numpy array indexing for a 2D array of shape [n_times, n_channels] except
        that scalar indexing returns a TimeSeries with singleton dimensions to preserve
        data type.

        The `timestamps` and `channel_data` attributes of the returned
        object are views of the original TimeSeries' attrributes. Therefore
        modifications directly to the attributes via the property-getter can result
        in unwanted side-effects (in which case make a deepcopy before proceeding!)

        Ex:
        ```
        >>> ts = TimeSeries(np.arange(4), np.arange(8).reshape((4, -1)))
        >>> ts.channel_data
        array([[0, 1],
               [2, 3],
               [4, 5],
               [6, 7]])
        >>> ts2 = ts[0:3, :]
        >>> ts2.channel_data
        array([[0, 1],
               [2, 3],
               [4, 5]])
        >>> # scalar casts to singleton
        >>> ts2 = ts[0, :]
        >>> ts2.channel_data
        array([[0, 1]])
        >>> # will throw an error...
        >>> ts.channel_data[0:2, :] = 1
        >>> ts.channel_data
        array([[1, 1],
               [1, 1],
               [4, 5],
               [6, 7]])
        >>> ts2.channel_data
        array([[1, 1],
               [1, 1],
               [4, 5]])
        # ts2's channel_data has also changed due to shared reference
        ```
        """
        time_indexer, channel_indexer = scalars_to_slice_indexer(indexer)
        return self.__class__(
            self.timestamps[time_indexer],
            self.channel_data[time_indexer, channel_indexer],
        )

    @property
    def shape(self):
        return self._channel_data.shape

    @classmethod
    def from_array(cls, array: np.ndarray) -> "TimeSeries":
        """
        Assume first column is time, all other is data
        """
        assert len(array.shape) == 2 and array.shape[1] >= 2
        return cls(array[:, 0], array[:, 1:])

    @classmethod
    def load(cls, filepath: str) -> "TimeSeries":
        with h5py.File(filepath, "r") as f:
            timestamps = f.get("timestamps").value
            channel_data = f.get("channel_data").value
        return cls(timestamps, channel_data)

    def save(self, filepath: str) -> None:
        with h5py.File(filepath, "w") as f:
            f.create_dataset("timestamps", data=self._timestamps)
            f.create_dataset("channel_data", data=self._channel_data)

    @property
    def timestamps(self) -> np.ndarray:
        return self._timestamps

    @timestamps.setter
    def timestamps(self, new_timestamps: np.ndarray) -> None:
        """
        Set the timestamps to new_timestamps, must be same length as before
        """
        if not is_valid_timestamps(new_timestamps):
            raise ValueError(
                "new_timestamps is either not 1D or not monotonically increasing"
            )
        elif len(self._timestamps) != len(new_timestamps):
            raise ValueError("new_timestamps has the incorrect shape!")
        self._timestamps = new_timestamps

    @property
    def channel_data(self) -> np.ndarray:
        return self._channel_data

    @channel_data.setter
    def channel_data(self, value: np.ndarray) -> None:
        """
        Set the channel_data, must be the same length as before
        """
        if len(value.shape) != 2:
            raise ValueError("value needs to be 2-dimensional")
        elif len(value) != len(self._channel_data):
            raise ValueError("value has wrong number of time points")
        self._channel_data = value

    @property
    def sample_rate(self) -> float:
        return 1.0 / np.mean(np.diff(self._timestamps))

    @property
    def time_series(self) -> np.ndarray:
        return np.hstack((self.timestamps.reshape((-1, 1)), self._channel_data))

    def select_channels(self, channel_selection: Index) -> "TimeSeries":
        """
        Return new TimeSeries with the selected channels only

        Args:
        ---
        `channel_selection` : Expression used to do basic indexing of
            a numpy array in a single dimension.

            - List, Tuple, np.ndarray type inputs can be integer and boolean
            masks.
            - Slicing operation (e.g. array[a:b] syntax) can be achieved through

            ```
            from data_view.array_utils import SliceMaker
            make_slice = SliceMaker()
            # select all but the last channel
            time_series.select_channels(make_slice[0:-2])
            ```

        Returns:
        ---
        A new `TimeSeries` objects with the selected channels.
        """
        return self[:, channel_selection]

    def select_time(self, time_selection: Index) -> "TimeSeries":
        """
        Return new TimeSeries with the selected time points only

        Args:
        ---
        `time_selection` : Expression used to do basic indexing of
            a numpy array in a single dimension.

            - List, Tuple, np.ndarray type inputs can be integer and boolean
            masks.
            - Slicing operation (e.g. array[a:b] syntax) can be achieved through

            ```
            from data_view.array_utils import SliceMaker
            make_slice = SliceMaker()
            # select all but last time point
            time_series.select_time(make_slice[0:-2])
            ```

        Returns:
        ---
        A new `TimeSeries` objects with the selected channels.
        """
        return self[time_selection, :]

    def select_channel_data_at_time(
        self,
        time_selection: Index,
        channel_selection: Index,
    ) -> "TimeSeries":
        """
        Return new TimeSeries with the selected time points and
        selected channels only

        Args:
        ---
        - `time_selection`, `channel_selection` :
            Expression used to do basic indexing of a numpy array in a single dimension.

            - List, Tuple, np.ndarray type inputs should be integers. If using boolean
                masking, can run into errors:

                "IndexError: shape mismatch: indexing arrays could not be broadcast
                together with shapes..."

                This is due to underlying numpy array indexing behavior,
                see https://stackoverflow.com/a/30176382

            - Slicing operation (e.g. array[a:b] syntax) can be achieved through
                `SliceMaker` similar to `select_time()` and `select_channels`.

            Example:
            ```
            from data_view.array_utils import SliceMaker
            make_slice = SliceMaker()
            # select all but last time point
            time_series.select_channel_data_at_time(
                make_slice[0:5], # select first 6 time points
                [0, 1, -1],      # select first 2 and last channel
            )
        """
        return self[time_selection, channel_selection]

    def transform_channel_data(
        self, func: Callable[[np.ndarray], np.ndarray]
    ) -> "TimeSeries":
        """
        Apply `func` on `channel_data`.

        If the transformed `channel_data` is 2D and has the same number
        of rows as before, a new `TimeSeries` with the transformed
        data and original `timestamps` is returned.

        This means if the `func` does not change the number of time points,
        a new `TimeSeries` is returned.

        Otherwise, the transformed `channel_data` is returned as an np.ndarray

        Ex.
        ```
        new_ts = ts.transform_channel_data(partial(scipy.stats.zscore, axis=0))
        ```
        returns a TimeSeries with the channels zscored in time.

        ```
        new_ts = ts.transform_channel_data(partial(np.mean, axis=1, keepdims=True))
        ```
        returns a TimeSeries with channel_data equal to the mean of `ts`'s channels.

        ```
        new_ts = ts.transform_channel_data(lambda x: np.vstack((x, x)))
        ```
        returns an np.ndarray equal to `np.vstack((ts.channel_data, ts.channel_data))`

        ```
        new_ts = ts.transform_channel_data(lambda x: np.hstack((x, x)))
        ```
        returns a TimeSeries with channel_data equal to
        `np.hstack((ts.channel_data, ts.channel_data))`

        """

        out = func(self._channel_data)
        if len(out.shape) < 2 or len(out) != len(self._timestamps):
            return out
        else:
            return self.__class__(self._timestamps, out)


class LabeledTimeSeries(TimeSeries):
    """
    Class to bundle TimeSeries with ChannelInfo object that
    gives information about each channel.

    The attributes of the ChannelInfo can be referred to with
    the same name from a LabeledTimeSeries.

    Ex.

    `lts` is a LabeledTimeSeries with the `channel_info` object:

    `lts = LabeledTimeSeries(timestamps, channel_data, channel_info)`

    The `detector_idx` property of `channel_info` can be referred to
    by `lts.detector_idx`.
    """

    # Addition to TimeSeries base class
    _channel_info: ChannelInfo

    """
    Methods inherited and not overridden from TimeSeries:
    - sample_rate
    """

    def __init__(
        self,
        timestamps: np.ndarray,
        channel_data: np.ndarray,
        channel_info: ChannelInfo,
    ) -> None:
        # In case we have single number as timestamps and channel_data
        timestamps = np.atleast_1d(timestamps)
        channel_data = np.atleast_1d(channel_data)

        # Check channel_info' shape and channel_data match,
        # and channel_info is right type
        if not issubclass(type(channel_info), ChannelInfo):
            raise TypeError("channel_info must be a ChannelInfo class")
        if len(channel_data.shape) != 2:
            raise ValueError("channel_data needs to have dimension [time, channels]")
        if len(channel_info) != channel_data.shape[1]:
            raise ValueError(
                "channel_data should have num of cols equal to length of ChannelInfo"
            )
        if not check_timestamps_and_data(timestamps, channel_data):
            raise ValueError("timestamps and channel_data are not compatible")

        self._channel_info = channel_info
        self._timestamps = timestamps
        self._channel_data = channel_data

    # __getstate__ and __setstate__ need to be set in order to pickle LTS
    # objects. Otherwise pickle attempts to call __getattr__ and runs into an
    # infinite loop.  # more information can be found here:
    # https://stackoverflow.com/questions/50888391/pickle-of-object-with-getattr-method-in-python-returns-typeerror-object-no/50888571#50888571
    def __getstate__(self):
        return vars(self)

    def __setstate__(self, state):
        vars(self).update(state)

    # Auto-generate properties from the ChannelInfo
    # `__getattr__` is only called if python can't find
    # the attribute via other means
    def __getattr__(self, name):
        """
        Ex. `my_labeled_time_series.channel_info.channel_attribute`
        is the same as `my_labeled_time_series.channel_attribute`
        """
        return getattr(self._channel_info, name)

    def __repr__(self):
        return (
            "LabeledTimeSeries (Time | Channels...)\n"
            + str(self.time_series)
            + "\nLabels\n"
            + str(self._channel_info)
        )

    def __eq__(self, other: "LabeledTimeSeries") -> bool:
        return super().__eq__(self, other) and self.channel_info == other.channel_info

    def __getitem__(self, indexer: Tuple[Index, Index]) -> "TimeSeries":
        """
        Return new LabeledTimeSeries with given time and channel selection. Syntax
        is the same as numpy array indexing for a 2D array of shape [n_times, n_channels]
        except that scalar indexing returns a LabeledTimeSeries with singleton dimensions
        to preserve data type.

        The `timestamps` and `channel_data` attributes of the returned
        object are views of the original LabeledTimeSeries' attrributes. Therefore
        modifications directly to the attributes via the property-getter can result
        in unwanted side-effects (in which case make a deepcopy before proceeding!)

        Ex:
        ```
        >>> ts = LabeledTimeSeries(np.arange(4), np.arange(8).reshape((4, -1)), channel_info)
        >>> ts.channel_data
        array([[0, 1],
               [2, 3],
               [4, 5],
               [6, 7]])
        >>> ts2 = ts[0:3, :]
        >>> ts2.channel_data
        array([[0, 1],
               [2, 3],
               [4, 5]])
        >>> # scalar casts to singleton
        >>> ts2 = ts[0, :]
        >>> ts2.channel_data
        array([[0, 1]])
        >>> # will throw an error...
        >>> ts.channel_data[0:2, :] = 1
        >>> ts.channel_data
        array([[1, 1],
               [1, 1],
               [4, 5],
               [6, 7]])
        >>> ts2.channel_data
        array([[1, 1],
               [1, 1],
               [4, 5]])
        # ts2's channel_data has also changed due to shared reference
        ```
        """
        time_indexer, channel_indexer = scalars_to_slice_indexer(indexer)
        return self.__class__(
            self.timestamps[time_indexer],
            self.channel_data[time_indexer, channel_indexer],
            self.channel_info[channel_indexer],
        )

    @classmethod
    def from_array(
        cls, array: np.ndarray, channel_info: ChannelInfo
    ) -> "LabeledTimeSeries":
        """
        Assume first column is time, all other is data
        """
        assert len(array.shape) == 2 and array.shape[1] >= 2
        return cls(array[:, 0], array[:, 1:], channel_info)

    @classmethod
    def from_hardware(
        cls,
        timestamps: np.ndarray,
        channel_data: np.ndarray,
        hardware: HardwareMetadata,
        channel_info: ChannelInfo,
    ) -> "LabeledTimeSeries":
        # Assume the ChannelInfo subclass implements `from_hardware` method
        channel_info = channel_info.from_hardware(hardware)
        return cls(timestamps, channel_data, channel_info)

    # Override load/save -- ChannelInfo has no load/save so..
    @classmethod
    def load(cls, filepath: str) -> "LabeledTimeSeries":
        raise NotImplementedError("LabeledTimeSeries.load is not implemented")

    def save(self, filepath: str) -> None:
        raise NotImplementedError("LabeledTimeSeries.save is not implemented")

    @property
    def channel_data(self) -> None:
        return self._channel_data

    @channel_data.setter
    def channel_data(self, value: np.ndarray) -> None:
        """
        Set the channel_data, must be the same shape as before to be
        consistent with channel_info
        """
        if len(value.shape) != 2:
            raise ValueError("value needs to be 2-dimensional")
        elif value.shape != self._channel_data.shape:
            raise ValueError(
                "value needs to be the same shape as the original channel-data"
            )
        self._channel_data = value

    @property
    def channel_info(self):
        return self._channel_info

    def select_channels(self, channel_selection: Index) -> "LabeledTimeSeries":
        """
        Return new LabeledTimeSeries with selected channels,
        timestamps is unchanged in the output.

        Args:
        ---
        - channel_selection: See `TimeSeries.select_channels`
        """
        return self[:, channel_selection]

    def select_time(self, time_selection: Index) -> "LabeledTimeSeries":
        """
        Return new LabeledTimeSeries with selected time points.
        Both timestamps and channel_data will be different in the output

        Args:
        ---
        - time_selection: See `TimeSeries.select_time`.
        """
        return self[time_selection, :]

    def select_channel_data_at_time(
        self,
        time_selection: Index,
        channel_selection: Index,
    ) -> "LabeledTimeSeries":
        """
        Return new LabeledTimeSeries with selected channels, at the selected
        time points.
        Both timestamps and channel_data will be different in the output

        Args: See `TimeSeries.select_channel_data_at_time`.
        """
        return self[time_selection, channel_selection]

    def transform_channel_data(
        self, func: Callable[[np.ndarray], np.ndarray]
    ) -> Union["LabeledTimeSeries", TimeSeries, np.ndarray]:
        """
        Apply `func` on `channel_data`.

        The output's type depends on whether the supplied `func` changes the number
        of rows (time points) and columns (channels) of `channel_data`.


                         |  preserve channels       | change channels
            -------------|--------------------------|--------------------------
            preserve time| `LabeledTimeSeries` with | TimeSeries with new
                         |  new channel_data, same  | channel_data, same
                         |  timestamps, same        | timestamps, no
                         |  channel_info            | channel_info
            -------------|----------------------------------------------------
            change time  | new data as np.ndarray   | new data as np.ndarray

        Ex.
        ```
        new_lts = lts.transform_channel_data(partial(scipy.stats.zscore, axis=0))
        ```
        returns a LabeledTimeSeries with the channels zscored in time.

        ```
        new_lts = lts.transform_channel_data(partial(np.mean, axis=1))
        ```
        returns a TimeSeries with channel_data equal to the mean of `lts`'s channels.
        The channel_info are lost in the process.

        ```
        new_lts = lts.transform_channel_data(lambda x: np.vstack((x, x)))
        ```
        returns an np.ndarray equal to `np.vstack((ts.channel_data, ts.channel_data))`

        ```
        # ts.channel_data has shape (5,5)
        new_lts = lts.transform_channel_data(lambda x: x[0:2, 0:2])
        ```
        returns an np.ndarray equal to `lts.channel_data[0:2, 0:2]`
        """

        out = func(self._channel_data)
        if len(out.shape) < 2 or len(out) != len(self._timestamps):
            # changes time
            return out
        elif out.shape[1] != len(self._channel_info):
            # changes channel
            return TimeSeries(self._timestamps, out)
        else:
            # preserve time and channel
            return self.__class__(self._timestamps, out, self._channel_info)


class StringLabeledTimeSeries(LabeledTimeSeries):
    """
    Class to handle simple labeling, e.g., just add the column names
    """

    # Addition to TimeSeries base class
    # _timestamps: np.ndarray
    # _channel_data: np.ndarray
    _channel_info: StringChannelInfo

    """
    Methods inherited from LabeledTimeSeries:
    - sample_rate
    """

    def __init__(
        self,
        timestamps: np.ndarray,
        channel_data: np.ndarray,
        channel_info: StringChannelInfo,
    ) -> None:
        timestamps = np.atleast_1d(timestamps)
        channel_data = np.atleast_1d(channel_data)
        # Check channel_info' shape and channel_data match,
        # and channel_info is right type
        if not issubclass(type(channel_info), ChannelInfo):
            raise TypeError("channel_info must be a ChannelInfo class")
        if len(channel_data.shape) != 2:
            raise ValueError("channel_data needs to have dimension [time, channels]")
        if len(channel_info) != channel_data.shape[1]:
            raise ValueError(
                "channel_data should have num of cols equal to length of ChannelInfo"
            )
        if not check_timestamps_and_data(timestamps, channel_data):
            raise ValueError("timestamps and channel_data are not compatible")

        self._channel_info = channel_info
        self._timestamps = timestamps
        self._channel_data = channel_data

    def from_hardware(self):
        """
        Forget this inherited class
        """
        print("not implemented, ignoring it")
        pass

    def select_channels_by_set(
        self, channel_set: Union[List[str], np.array]
    ) -> "StringLabeledTimeSeries":
        """
        An easier wrapper for select_channels, example usage
        `time_series2 = time_series1.select_channels_by_set(['LEFT_INDEX'])`
        Inputs:
            channel_set, a list of channel names, or an np.array of strings
        Output: StringLabeledTimeSeries
        """
        return self[:, np.in1d(self.channel_info.column_names, channel_set)]
