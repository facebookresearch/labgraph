#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Dict, List, Union

SerializedGraph = Dict[
    str,
    Union[
        str,
        List[
            Dict[
                str,
                Union[
                    List[str],
                    List[Dict[str, str]]
                ]
            ]
        ]
    ]
]
