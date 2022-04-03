#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Dict, List, Union

"""
{
    name: "message_name",
    fields: {
            "field_name": "field_type",
            ...
    }
}
"""

SerializedMessage = Dict[
    str,
    Union[
        str,
        Dict[str, str]
    ]
]


"""
{
    name: "graph_name",
    nodes: {
        "node_name":{
            upstreams:{
                "upstream_name":[
                    SerializedMessage,
                ],
                ...
            }
        }
    }
}
"""
SerializedGraph = Dict[
    str,
    Union[
        str,
        Dict[
            str,
            Dict[
                str,
                Dict[
                    str,
                    List[SerializedMessage]
                ]
            ]
        ]
    ]
]
