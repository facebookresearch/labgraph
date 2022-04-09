#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

"""Filling out a docstring with identifier placeholders.

The docstring filling decorator and associated functions are based off
scipy._lib.doccer, which has been moved to an internal location in scipy.
"""

from typing import Any, Callable, Dict

__all__ = ["fill_in_docstring"]

AnyFunction = Callable[[Any], Any]


def fill_in_docstring(keywords: Dict[str, str]) -> Callable[[AnyFunction], AnyFunction]:
    """Replace identifiers like `{ident}` in a docstring.

    Parameters
    ----------
    keywords : Dict[str, str]
        A mapping from identifiers to strings.

    Returns
    -------
    decorator
        A decorator that will replace f-string like identifiers in a docstring.

    Example
    -------
    >>> common_doc = fill_in_docstring({'ident': 'This identifier '})
    >>>
    >>> @common_doc
    ... def f(x):
    ...     '''{ident} is common between functions!'''
    ...     pass
    >>>
    >>> f.__doc__ == "This identifier is common between functions!"
    True
    """

    def _docfill(f):
        f.__doc__ = f.__doc__.format(
            **{
                identifier: description.rstrip()
                for identifier, description in keywords.items()
            }
        )
        return f

    return _docfill
