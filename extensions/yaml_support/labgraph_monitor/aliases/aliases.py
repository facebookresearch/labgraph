#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

from typing import Dict, List, Union


"""
{
    name: "graph_name",
    nodes: {
        "node_name":{
            upstreams:{
                "upstream_name":[
                    {
                        name: "message_name",
                        type: "message_type",
                    }
                ]
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
                    List[Dict[str, str]]
                ]
            ]
        ]
    ]
]
