#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from ..doc.docfill import fill_in_docstring

__all__ = ["data_view_common_docs"]

data_view_common_docs = fill_in_docstring(
    {
        "size": """size: int
        The size of each chunk
        """,
        "step": """step: int
        How much to move by when taking a chunk.
        """,
        "ragged": """ragged: bool, optional, default False
        If true, the last chunk could be smaller than the specified size. If
        false, the last chunk that would have a number of element fewer than size
        is discarded.
        """,
    }
)
