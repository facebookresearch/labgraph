#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Any, Dict, List, Optional, Union

import numpy as np

from ..data_view.array_utils import is_one_axis_array


class ChannelInfo(object):
    """
    This is a parent class to represent different sensor
    modality's channel information.

    A `ChannelInfo` object can combine with a `TimeSeries` to form
    `LabeledTimeSeires`, where each column of the `TimeSeries`'
    `channel_data` can be described by each "row" of the
    `ChannelInfo`.

    The individual "columns" of attributes can be accessed by
    `my_channelinfo.myattr`.

    Slicing by different channels (or "rows") is supported, e.g.
    `my_channelinfo[0:2]` will return a new `ChannelInfo` object
    with the information about the first two channels only.

    All properties/attributes are readonly.

    Note that for each specific sensor modality, `ChannelInfo` should
    be subclassed (e.g. `DOTChannelInfo`). The child class should
    provide and instantiate the attributes in the constructor, and
    provide its generation from `HardwareMetadata`, if applicable.
    """

    info_type: str
    n_channels: int

    def __init__(self, info_type: str, n_channels: int = 0) -> None:
        """
        Args:
        ---
        info_type: str, to describe the ChannelInfo
        n_channels: int. Number of channels
        """
        self.info_type = info_type
        self.n_channels = n_channels

    def __repr__(self) -> str:
        info_array = self.info_array
        if len(info_array) == 0:
            return f"{self.info_type}: Empty"
        header = "|".join(info_array.dtype.names)
        return f"{self.info_type}\n{header}\n{info_array}"

    @property
    def info_array(self) -> np.recarray:
        # Return the recarray formed from the ndarray attributes
        # Preserving dtype
        columns = []
        header = ""
        for k, v in self.__dict__.items():
            if type(v) != np.ndarray:
                continue
            header += k + ", "
            columns.append(v)
        return np.core.records.fromarrays(columns, names=header)

    # All properties are readonly! And I don't want to make and decorate
    # a new method for each property
    def __setattr__(self, name: str, value: any) -> None:
        if name in self.__dict__:
            raise AttributeError(
                f"Forbidden to set attributes for {self.__class__.__name__}"
            )
        else:
            self.__dict__[name] = value

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"Forbidden to delete attributes from {self.__class__.__name__}"
        )

    def __eq__(self, other: "ChannelInfo") -> bool:
        same = True
        for index, (value, other_value) in enumerate(
            zip(self.__dict__.values(), other.__dict__.values())
        ):
            if index < 2:
                # ignore baseclass init arguments
                continue
            same &= np.array_equal(value, other_value)

        return same

    def __hash__(self) -> int:
        hash_values = []
        for _, value in sorted(vars(self).items()):
            if isinstance(value, np.ndarray):
                hash_values.append(value.data.tobytes())
            else:
                hash_values.append(value)
        return hash(tuple(hash_values))

    def __getitem__(self, key: Union[List, slice, np.ndarray, int]) -> Any:
        func_args = []
        # Class attribute definition order is preserved iin __dict__
        # per PEP0520 (https://www.python.org/dev/peps/pep-0520/)
        for index, value in enumerate(self.__dict__.values()):
            if index < 2:
                # ignore baseclass init arguments
                continue
            if type(value) is np.ndarray:
                func_args.append(np.atleast_1d(value[key]))
            else:
                func_args.append(value)
        return self.__class__(*func_args)

    def check_and_assign(
        self, var_name: str, value: np.ndarray, var_dtype: np.dtype
    ) -> None:
        if value.dtype != var_dtype:
            raise TypeError(f"{var_name}.dtype != {var_dtype}")
        setattr(self, var_name, value)

    def __len__(self):
        # len(channel_info) returns number of channels
        return self.n_channels


class DOTChannelInfo(ChannelInfo):
    # Inherited properties
    # info_type: str

    # Properties
    detector_idx: np.ndarray  # int
    source_idx: np.ndarray  # int
    distance: np.ndarray  # float
    source_x: np.ndarray  # int
    source_y: np.ndarray  # int
    source_z: np.ndarray  # int
    detector_x: np.ndarray  # float
    detector_y: np.ndarray  # float
    detector_z: np.ndarray  # float
    carrier_freq: np.ndarray  # float
    carrier_freq_idx: np.ndarray  # int
    wavelength: np.ndarray  # float
    subdevice_idx: np.ndarray  # int

    # The entries here is {wavelength_idx:wavelength}
    # such as {0 : 830.0, 1 : 685.0}
    wavelength_table: Dict[int, float]

    # Include device name which is useful for any dependent processing
    device_name: str

    def __init__(
        self,
        detector_idx: np.ndarray,
        source_idx: np.ndarray,
        distance: np.ndarray,
        source_x: np.ndarray,
        source_y: np.ndarray,
        source_z: np.ndarray,
        detector_x: np.ndarray,
        detector_y: np.ndarray,
        detector_z: np.ndarray,
        carrier_freq: np.ndarray,
        carrier_freq_idx: np.ndarray,
        wavelength: np.ndarray,
        subdevice_idx: np.ndarray,
        wavelength_table: Dict[int, float],
        device_name: Optional[str] = None,
    ):
        # args checking
        # check all arguments are the same length
        args = list(locals().values())
        args = [x for x in args if type(x) == np.ndarray]

        # make sure they are all 1D arrays
        if not all(is_one_axis_array(x) for x in args):
            raise ValueError("The inputs need to have all elements on the same axis")
        # make sure they are the same length
        args_len = np.array([x.size for x in args if type(x) == np.ndarray])
        if not np.all(args_len == args_len[0]):
            raise ValueError("The inputs need to all have the same length!")
        super().__init__("Flattened DOT", args_len[0])

        # assign them to things
        self.check_and_assign("detector_idx", detector_idx, "int")
        self.check_and_assign("source_idx", source_idx, "int")
        self.check_and_assign("distance", distance, "float")
        self.check_and_assign("source_x", source_x, "float")
        self.check_and_assign("source_y", source_y, "float")
        self.check_and_assign("source_z", source_z, "float")
        self.check_and_assign("detector_x", detector_x, "float")
        self.check_and_assign("detector_y", detector_y, "float")
        self.check_and_assign("detector_z", detector_z, "float")
        self.check_and_assign("carrier_freq", carrier_freq, "float")
        self.check_and_assign("carrier_freq_idx", carrier_freq_idx, "int")
        self.check_and_assign("wavelength", wavelength, "float")
        self.check_and_assign("subdevice_idx", subdevice_idx, "int")
        self.wavelength_table = wavelength_table
        self.device_name = device_name

    def __repr__(self):
        return (
            f"Device={self.device_name}\n"
            + super().__repr__()
            + f"\nwavelength_table: {self.wavelength_table}"
        )


class Metric2ChannelInfo(ChannelInfo):
    # Essentially the same as DOTChannelInfo, but now
    # labels whether a channel corresponds to Metric1 or not

    # Inherited property
    # info_type: str

    # Propertys
    detector_idx: np.ndarray  # int
    source_idx: np.ndarray  # int
    distance: np.ndarray  # float
    source_x: np.ndarray  # int
    source_y: np.ndarray  # int
    source_z: np.ndarray  # int
    detector_x: np.ndarray  # float
    detector_y: np.ndarray  # float
    detector_z: np.ndarray  # float
    is_Metric1: np.ndarray  # bool -- True if Metric1, False if HbR
    subdevice_idx: np.ndarray  # int

    # Include device name which is useful for any dependent processing
    device_name: str

    def __init__(
        self,
        detector_idx: np.ndarray,
        source_idx: np.ndarray,
        distance: np.ndarray,
        source_x: np.ndarray,
        source_y: np.ndarray,
        source_z: np.ndarray,
        detector_x: np.ndarray,
        detector_y: np.ndarray,
        detector_z: np.ndarray,
        is_Metric1: np.ndarray,
        subdevice_idx: np.ndarray,
        device_name: Optional[str] = None,
    ):
        # args checking
        # check all arguments are the same length
        args = list(locals().values())
        args = [x for x in args if type(x) == np.ndarray]

        # make sure they are all 1D arrays
        if not all(is_one_axis_array(x) for x in args):
            raise ValueError("The inputs need to have all elements on the same axis")
        # make sure they are the same length
        args_len = np.array([x.size for x in args if type(x) == np.ndarray])
        if not np.all(args_len == args_len[0]):
            raise ValueError("The inputs need to all have the same length!")
        super().__init__("Flattened Metric2 data", args_len[0])

        # assign them to things
        self.check_and_assign("detector_idx", detector_idx, "int")
        self.check_and_assign("source_idx", source_idx, "int")
        self.check_and_assign("distance", distance, "float")
        self.check_and_assign("source_x", source_x, "float")
        self.check_and_assign("source_y", source_y, "float")
        self.check_and_assign("source_z", source_z, "float")
        self.check_and_assign("detector_x", detector_x, "float")
        self.check_and_assign("detector_y", detector_y, "float")
        self.check_and_assign("detector_z", detector_z, "float")
        self.check_and_assign("is_Metric1", is_Metric1, "bool")
        self.check_and_assign("subdevice_idx", subdevice_idx, "int")
        self.device_name = device_name

    def __repr__(self):
        return f"Device={self.device_name}" + super().__repr__()


class StringChannelInfo(ChannelInfo):
    """
    This is to generate a generic ChannelInfo class that specify column names of a
    a time series, To be added
    """

    column_names: Union[List[str], np.array]

    def __init__(self, column_names: Union[List[str], np.array]) -> None:
        if type(column_names) is list:
            column_names = np.array(column_names, dtype="U32")
        if not is_one_axis_array(column_names):
            raise ValueError("column_names must be 1D")
        super().__init__("column_names", len(column_names))
        self.check_and_assign("column_names", column_names, "U32")
