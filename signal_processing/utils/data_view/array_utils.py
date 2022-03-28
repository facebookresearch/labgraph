#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import multiprocessing
from enum import Enum, auto
from itertools import count, product
from numbers import Number
from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Optional,
    Union,
    List,
    Tuple,
    Dict,
    TypeVar,
)

import numpy as np
from skimage.util import view_as_windows

from ._data_view_common_docs import data_view_common_docs

"""
This file holds simple utility functions for operations on numpy arrays.
"""

A = TypeVar("A")
Index = Union[int, List, Tuple, slice, np.ndarray]
Indexer = Union[Index, Tuple[Index, ...]]


def is_index(value) -> bool:
    return type(value) in (int, list, tuple, slice, np.ndarray)


def is_indexer(value) -> bool:
    if type(value) is tuple:
        return all(is_index(v) for v in value)
    else:
        return is_index(value)


def check_index(index: Index) -> "Index":
    if not is_index(index):
        raise IndexError(
            "Index '{}' is not one of the valid index types: "
            "[int, list, tuple, slice, np.ndarray]".format(index)
        )
    else:
        return index


def check_indexer(indexer: Indexer, ndim: int = 2) -> "Indexer":
    if not is_indexer(indexer):
        raise IndexError(
            "Indexer '{}' is not one of the valid indexer types: "
            "[Index, Tuple[Index, ...]]".format(indexer)
        )
    if type(indexer) is tuple:
        length = len(indexer)
    else:
        indexer, length = (indexer,), 1
    if not length == ndim and ndim is not None:
        raise IndexError(
            "Expected indexer of length '{}' but got indexer of length '{}'.".format(
                ndim, len(indexer)
            )
        )

    return indexer


def is_one_axis_array(x: np.ndarray) -> bool:
    """Evaluate whether the input array has multiple elements only along one axis

    Example:

    a.shape = (0,) -> True
    a.shape = (5,) -> True
    a.shape = (1,) -> True
    a.shape = (5,1) -> True
    a.shape = (1,5) -> True
    a.shape = (5,2) -> False
    a.shape = (1,1,5) -> True
    a.shape = (2,1,5) -> False
    a.shape = (1,1,1,1) -> True

    Args:
    ----
    x: np.ndarray, input array to evaluate

    Returns:
    ----
    Returns true if input array has multiple elements only along one axis
    """

    x_dims = x.shape
    # case is when x is one dimensional
    if len(x_dims) == 1:
        return True
    # case when x has only one element, dimension doesn't matter then
    if x.size == 1:
        return True

    # otherwise, x_dims should have none-1's at all except for one value
    return np.sum(np.array(x_dims) > 1) == 1


def d1_to_col(array: np.ndarray) -> np.ndarray:
    """
    If 1D array, convert to column.
    Otherwise return itself
    """
    if len(array.shape) < 2:
        return array.reshape((-1, 1))
    else:
        # print("array not 1D, do nothing")
        return array


def d1_to_row(array: np.ndarray) -> np.ndarray:
    """
    If 1D array, convert to row.
    Otherwise return itself
    """
    if len(array.shape) < 2:
        return array.reshape((1, -1))
    else:
        # print("array not 1D, do nothing")
        return array


def scalar_to_array(value) -> np.ndarray:
    if np.isscalar(value):
        return np.atleast_1d(value)
    else:
        return value


def scalar_to_slice_index(value: Index) -> "Index":
    value = check_index(value)
    if type(value) is int:
        return slice(value, value + 1, 1)
    else:
        return value


def scalars_to_slice_indexer(value: Indexer, ndim: int = 2) -> "Indexer":
    if not type(value) is tuple:
        indexer = scalar_to_slice_index(check_indexer(value))
    else:
        indexer = tuple(scalar_to_slice_index(v) for v in check_indexer(value))

    return check_indexer(indexer, ndim=ndim)


def raise_1d_to_2d(array: np.ndarray) -> np.ndarray:
    # Raise 1D array to 2D array with singleton dimension on right
    assert array.ndim == 1 or array.ndim == 2
    if array.ndim == 1:
        array = array[:, None]

    return array


def diagflat(v: np.ndarray, k: int = 0) -> np.ndarray:
    """Wraps "np.diagflat" for >= 2D inputs."""
    # Transform flat array to diagonal matrix
    v = (
        np.diagflat(v, k=k)
        if v.ndim == 1
        else v[..., None] * np.eye(v.shape[-1], k=k)[(v.ndim - 1) * (None,)]
    )

    return v


def diagonal(v: np.ndarray, k: int = 0) -> np.ndarray:
    """Wraps "np.diagonal" for >= 2D inputs."""
    # Transform diagonal matrix to flat array
    v = np.diagonal(v, offset=k, axis1=-2, axis2=-1)

    return v


def upcast_ndim(x: np.ndarray, ndim: int) -> np.ndarray:
    """Upcast array to dimensionality.

    NumPy matrix operations typically allow array broadcasting such that dimensions between two arrays can either
    match or equal 1.

    Additionally, dimensions on the left may be missing from the left on one of two arrays, which would otherwise
    satisfy the aforementioned constraints. In this case, the lower-rank array is treated as if it had singleton
    dimensions to its left, which is equivalent to "upcasting". This allows for matrix operations on arrays of differing
    ranks but otherwise compatible shapes.

    For more info, see https://numpy.org/doc/stable/user/basics.broadcasting.html.

    For example: np.ones((8, 4, 5, 1)) * np.ones((4, 1, 10)) -> np.ones((8, 4, 5, 10))

    Args:
    ----
    x: np.ndarray, input array to upcast
    ndim: int, dimensionality to upcast to

    Returns:
    ----
    Returns upcasted input array
    """
    # Upcast array to dimensionality
    shape = (ndim - x.ndim) * (1,) + x.shape
    if not x.shape == shape:
        x = x.reshape(shape)

    return x


def upcast_tile(x: np.ndarray, shape: Tuple) -> np.ndarray:
    """Upcasts and tiles array to be match given shape.

    For NumPy operations that don't support flexible array broadcasting, it may also be necessary to ensure both arrays
    have identical shapes. Singleton dimensions can simply be tiled to match the shape of the other array.

    For example: {np.ones((4, 5, 1)), (4, 1, 10)} -> np.ones((4, 5, 10))


    Args:
    ----
    x: np.ndarray, input array to upcast and tile

    Returns:
    ----
    Returns upcasted and tile input array
    """
    # Upcast array then tile singleton dimensions
    x = upcast_ndim(x, len(shape))
    if not x.shape == shape:
        assert not any(not xs == s and not xs == 1 for xs, s in zip(x.shape, shape))
        x = np.tile(x, [1 if xs == s else s for xs, s in zip(x.shape, shape)])

    return x


class SliceMaker(object):
    """
    Utility to enable using slice syntax in functions
    """

    def __getitem__(self, item):
        return item


"""
Object that can be used to generate slice object via
numpy style slicing notation.

Ex.
    ```
    >>> array = np.ones((5))
    >>> new_array = array[make_slice[0:3]]
    >>> new_array
    array([1., 1., 1.])
    ```
Use this for the `select_x` methods in `TimeSeries` classes
"""
make_slice = SliceMaker()


"""
Function that act as masks that operate on numpy arrays,
convenience functions to serve as partial functions
"""


def equal_mask(x: np.ndarray, target: float) -> np.ndarray:
    return x == target


def less_mask(x: np.ndarray, target: float) -> np.ndarray:
    return x < target


def greater_mask(x: np.ndarray, target: float) -> np.ndarray:
    return x > target


def le_mask(x: np.ndarray, target: float) -> np.ndarray:
    return x <= target


def ge_mask(x: np.ndarray, target: float) -> np.ndarray:
    return x >= target


class IntervalTypes(Enum):
    CLOSED_OPEN = auto()  # [a, b)
    OPEN_CLOSED = auto()  # (a, b]
    CLOSED_CLOSED = auto()  # [a, b]
    OPEN_OPEN = auto()  # (a, b)


def closed_open_range_mask(
    x: np.ndarray, end_points: Tuple[float, float]
) -> np.ndarray:
    return (x >= end_points[0]) & (x < end_points[1])


def open_closed_range_mask(
    x: np.ndarray, end_points: Tuple[float, float]
) -> np.ndarray:
    return (x > end_points[0]) & (x <= end_points[1])


def closed_closed_range_mask(
    x: np.ndarray, end_points: Tuple[float, float]
) -> np.ndarray:
    return (x >= end_points[0]) & (x <= end_points[1])


def open_open_range_mask(x: np.ndarray, end_points: Tuple[float, float]) -> np.ndarray:
    return (x > end_points[0]) & (x < end_points[1])


@data_view_common_docs
def chunk(
    arr: A,
    size: int,
    step: int = 1,
    ragged: bool = False,
    slice_function: Optional[Callable[[A, int, int], A]] = None,
    len_function: Optional[Callable[[A], int]] = None,
) -> Iterator[A]:
    """Chunk an array into `size` segments every `step` elements.

    Parameters
    ----------
    arr: A
        Any object on which the provided slice_function and len_function
        operate on.
    {size}
    {step}
    {ragged}
    slice_function: Optional[Callable[[A, int, int], A]]
        The function that can be used to slice the input array `arr` into
        segments. If no slice function is specified, `__slice__` is called.
    len_function: Optional[Callable[[A], int]]
        The function that can be used to get the length of the input array
        `arr`. If no length function is specified, `__len__` is called.

    Examples
    --------
    >>> import numpy as np
    >>> list(chunk(np.arange(0, 10), 4, 2))
    [array([0, 1, 2, 3]),
     array([2, 3, 4, 5]),
     array([4, 5, 6, 7]),
     array([6, 7, 8, 9])]

    See Also
    --------
    skimage.view_as_windows: Rolling window view of the input n-dimensional array
    """
    # These default functions work for 1D numpy arrays
    # as well as lists and tuples.
    if slice_function is None:

        def slice_function(x, start, stop):
            return x[start:stop]

    if len_function is None:

        def len_function(x):
            return len(x)

    arr_len = len_function(arr)

    def compare_value(k):
        return k if ragged else k + size - 1

    for k in count(start=0, step=step):
        if compare_value(k) >= arr_len:
            break
        else:
            yield slice_function(arr, k, k + size)


# I stole these functions from https://stackoverflow.com/a/45555516


def _unpacking_apply_along_axis(
    all_args: Tuple[Callable, int, np.ndarray, Tuple, Dict]
) -> np.ndarray:
    """
    Like numpy.apply_along_axis(), but with arguments in a tuple
    instead.

    This function is useful with multiprocessing.Pool().map(): (1)
    map() only handles functions that take a single argument, and (2)
    this function can generally be imported from a module, as required
    by map().
    """
    (func1d, axis, arr, args, kwargs) = all_args
    return np.apply_along_axis(func1d, axis, arr, *args, **kwargs)


def parallel_apply_along_axis(
    func1d: Callable,
    axis: int,
    arr: np.ndarray,
    *args: Tuple,
    pool: Optional["multiprocessing.Pool"] = None,
    **kwargs: Dict
) -> np.ndarray:
    """
    Like numpy.apply_along_axis(), but takes advantage of multiple
    cores.
    """
    # Effective axis where apply_along_axis() will be applied by each
    # worker (any non-zero axis number would work, so as to allow the use
    # of `np.array_split()`, which is only done on axis 0):
    effective_axis = 1 if axis == 0 else axis
    if effective_axis != axis:
        arr = arr.swapaxes(axis, effective_axis)

    # Chunks for the mapping (only a few chunks):
    chunks = [
        (func1d, effective_axis, sub_arr, args, kwargs)
        for sub_arr in np.array_split(arr, multiprocessing.cpu_count())
    ]

    if pool is None:
        pool = multiprocessing.Pool()
        close_pool = True
    else:
        close_pool = False

    individual_results = pool.map(_unpacking_apply_along_axis, chunks)

    # Freeing the workers:
    if close_pool:
        pool.close()
        pool.join()

    return np.concatenate(individual_results)


def grouped(iterable: Iterable[Any], n: int) -> Iterable[Iterable[Any]]:
    "s -> (s0,s1,s2,...sn-1), (sn,sn+1,sn+2,...s2n-1), (s2n,s2n+1,s2n+2,...s3n-1), ..."
    return zip(*[iter(iterable)] * n)


def nan_like(target: Union[Number, np.ndarray]) -> Union[Number, np.ndarray]:
    if isinstance(target, Number):
        return np.nan
    elif isinstance(target, np.ndarray):
        out = np.empty(target.shape)
        out[:] = np.nan
        return out
    else:
        raise ValueError("Target is not supported")


def window_inplace(
    x: np.ndarray, window: Union[int, Tuple[int, int]], causal: bool = False
) -> np.ndarray:
    """Wrapper around "skimage.util.view_as_windows" to support arbitray, causal or acausal window shifts.

    The window should either be an integer sample size or a tuple with inclusive left and right bounds relative to
    the current sample (considered as 0). The latter allows for arbitrarily time-shifted and asymmetric windows.

    Windowing with a for loop and copy is slow and memory-hungry. For an arbitrary array with window W, the size
    of the array in memory increases by a factor of W. For large arrays, this can easily fill up RAM. Instead of
    copying, one can instead take a strided view into the array that simply repeats the indices to simulated the
    windowed array in place without reallocating memory.

    Args:
    ----
    x: np.ndarray, input array to window
    window: int or tuple pair of ints, window size or inclusive window bounds relative to current sample
    causal: bool, when using an integer window whether to distribute the samples causally or not

    Returns:
    ----
    Returns windowed input array
    """
    # Window in-place (without copying) using memory-efficient stride tricks
    if type(window) is int:
        window = (
            (-((window - 1) // 2), (window - 1) // 2 + (window - 1) % 2)
            if not causal
            else (-window + 1, 0)
        )
    assert window[0] <= window[1]
    x = np.pad(
        x,
        ((-min(window[0], 0), max(window[1] - 1, 0) + 1),) + (x.ndim - 1) * ((0, 0),),
        mode="constant",
    )
    w = view_as_windows(x, (window[1] - window[0] + 1,) + x.shape[1:])[
        None if window[0] < 0 else window[0] : None if window[1] > 0 else window[1] - 1
    ]
    if x.ndim > 1:
        w = w.squeeze(axis=tuple(range(1, x.ndim)))
    w = w.transpose((0,) + tuple(range(2, w.ndim)) + (1,))

    return w


def mix_array(
    x: np.ndarray,
    nrepeat: Optional[int] = None,
    axis: Tuple[int, int] = (0, -1),
    mixing: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Multiplies ND array by an independent 2D mixing matrix.

    Consider the simplest block-diagonal (mixing) matrix, the identity matrix, for example:
    [[1, 0, 0, 0, 0, 0],
     [0, 1, 0, 0, 0, 0],
     [0, 0, 1, 0, 0, 0],
     [0, 0, 0, 1, 0, 0],
     [0, 0, 0, 0, 1, 0],
     [0, 0, 0, 0, 0, 1]]
    This constitutes no effective mixing or scaling.

    An arbitrary block-diagonal matrix contains sub-matrices (blocks) >= 1 x 1 placed along the diagonal as so:
    [[A, 0, 0]]
    [[0, B, 0]]
    [[0, 0, c]]

    In practice, the blocks can be of varying (but always rectangular) shapes.
    [[6, 4, 0, 0, 0, 0],
     [2, 1, 0, 0, 0, 0],
     [0, 0, 1, 1, 4, 0],
     [0, 0, 3, 8, 5, 0],
     [0, 0, 6, 7, 1, 0],
     [0, 0, 0, 0, 0, 1]]

    However, unlike "scipy.linalg.block_diag," the mixing matrix need not be a block-digonal matrix, and can instead
    mixing the array with arbitray mixing patterns.

    Args:
    ----
    x: np.ndarray, input array to mix
    nrepeat: int, number of times to effectively repeat array when using the default identity mixing matrix
    axis: tuple, pair of axes to multiply mixing matrix with, with the latter being repeated 2nd dimension of mixing
    matrix # of times
    mixing: np.ndarray, mixing matrix to multiply input array with

    Returns:
    ----
    Returns mixed input array
    """
    # Parse axes
    assert x.ndim >= 2
    assert len(axis) == 2
    axis = [ax % x.ndim for ax in axis]
    if axis[0] == axis[1]:
        x = x[(axis[1] + 1) * (slice(None, None, None),) + (None,)]
    if nrepeat is None:
        nrepeat = x.shape[axis[0]]
    assert nrepeat == x.shape[axis[0]] or x.shape[axis[0]] == 1 or nrepeat == 1

    # Apply mixing matrix
    x = x[(axis[1] + 1) * (slice(None, None, None),) + (None,)]
    if mixing is None:
        mixing = np.eye(nrepeat)
    else:
        assert mixing.ndim == 2
    mixing = mixing[
        (min(axis) + int(axis[1] < axis[0])) * (None,)
        + (slice(None, None, None),)
        + (abs(axis[1] - axis[0]) - int(axis[1] < axis[0])) * (None,)
        + (slice(None, None, None),)
    ]
    x = x * mixing
    x = x.reshape(x.shape[: axis[1]] + (-1,) + x.shape[axis[1] + 2 :])

    return x


def upcast_apply(
    func: Callable[[Any], Any],
    *args: Tuple,
    narr: Optional[int] = None,
    sub_ndim: int = 2,
    **kwargs: Dict
) -> Optional[Any]:
    """
    Allows normally *D-only (typically linear algebra) functions to support ND inputs. Many, but not all, NumPy and
    SciPy functions support this natively for functions that normally operate on 2D inputs.

    Args:
    ----
    func: callable, function to call on *D slices of upcasted input arrays
    *args: variable arguments, arrays to provide function followed by any positional arguments
    narr: int, number of positional arguments to consider to be arrays (otherwise inferred)
    sub_ndim: int, dimensionality of array slices to provide function
    **kwargs: variable named arguments, named keyword arguments to provide function

    Returns:
    ----
    Returns mixed input array
    """
    # Parse arrays
    if narr is None:
        arr = ()
        for i, arg in enumerate(args):
            if isinstance(arg, np.ndarray):
                arr += (arg,)
            else:
                args = args[i:]
                break
    else:
        arr, args = args[:narr], args[narr:]
    ndim = max(a.ndim for a in arr)
    assert ndim >= sub_ndim

    # Cast inputs as needed then apply function
    if ndim == 2:
        out = func(*(arr + args), **kwargs)
    else:
        arr = tuple(upcast_ndim(a, ndim) for a in arr)
        assert not any(
            not all((s[0] == ss for ss in s or s[0] == 1 or ss == 1) for ss in s)
            for s in zip(*[a.shape[:-sub_ndim] for a in arr])
        )
        samples = tuple(
            max(sample) for sample in zip(*[a.shape[:-sub_ndim] for a in arr])
        )
        out = [
            func(
                *[
                    a[tuple(index % s for index, s, in zip(indices, a.shape))]
                    for a in arr
                ],
                **kwargs
            )
            for indices in product(*[range(sample) for sample in samples])
        ]
        if not isinstance(out[0], tuple):
            out = np.array(out)
        else:
            for (
                i,
                o,
            ) in enumerate(zip(*out)):
                if not o[0].shape:
                    out[i] = np.reshape(o, samples)
                elif len(o[0]):
                    out[i] = np.reshape(o, samples + o[0].shape)
                else:
                    shape, slc = zip(
                        *[
                            (s, slice(None, None, None))
                            if s
                            else (1, slice(0, 0, None))
                            for s in o[0].shape
                        ]
                    )
                    slc = len(samples) * (slice(None, None, None),) + slc
                    out[i] = np.empty(samples + shape)[slc]

    return out
