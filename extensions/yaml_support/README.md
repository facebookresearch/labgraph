# YAML Support for LabGraph

This extension provides an API to generate a serialized version of the labgraph topology. The serialized graph topology can be used in different applications E.g: server-client communication or to get a simplified overview of the topology in case of complicated graphs.

## Quick Start

### Method 1 - building from source code

**Prerequisites**:
* Python3\
Supported python version(s)
    * [Python3.6](https://www.python.org/downloads/)
    * [Python3.8](https://www.python.org/downloads/) (**RECOMMENDED**)
* Make sure to install [labgraph](https://github.com/facebookresearch/labgraph) before proceeding

```
cd labgraph/extensions/yaml_support
python setup.py install
```

### Testing:

To make sure things are working:

1- Move to the root of the LabGraph directory:
```
labgraph\extensions\yaml_support> cd ../..
labgraph>
```
2- Run the following tests
```
python -m extensions.yaml_support.labgraph_monitor.tests.test_lg_monitor_api
```
```
python -m extensions.yaml_support.labgraph_yaml_parser.tests.test_lg_yaml_api
```

### API

#### Labgraph Monitor:

**generate_labgraph_monitor(graph: lg.Graph) -> None** : This function can be used to generate a serialized version of the passed graph instance. The serialized version of the graph will be streamed
to the clients using LabGraph Websockets API.

1. Call **generate_labgraph_monitor(graph: lg.Graph) -> None** and pass an instance of the graph as a parameter
```
from extensions.yaml_support.labgraph_monitor.generate_lg_monitor.generate_lg_monitor import (
    generate_labgraph_monitor
)

generate_labgraph_monitor(graph)
```

This will start a websocket server on localhost port 9000 (127.0.0.1:9000)

2. To start receiving data from the server, send the following `StartStreamRequest` to **ws://127.0.0.1:9000**
```
{
   "api_version": "0.1",
   "api_request": {
     "request_id": 1,
     "start_stream_request": {
       "stream_id": "LABGRAPH.MONITOR",
        "labgraph.monitor": {
        }
     }
   }
}
```

A serialized representation of the graph should be received each 200ms

The graph representation has the following schema: 
```
{
    "stream_batch": {
        "stream_id": "LABGRAPH.MONITOR",
        "labgraph.monitor": {
            "samples": [
                {
                    "data": {
                        "name": "Demo",
                        "nodes": {
                            "NoiseGenerator": {
                                "inputs": [],
                                "upstreams": []
                            },
                            "RollingAverager": {
                                "inputs": [
                                    {
                                        "name": "INPUT",
                                        "type": "RandomMessage"
                                    }
                                ],
                                "upstreams": [
                                    "NoiseGenerator"
                                ]
                            },
                            "Amplifier": {
                                "inputs": [
                                    {
                                        "name": "INPUT",
                                        "type": "RandomMessage"
                                    }
                                ],
                                "upstreams": [
                                    "NoiseGenerator"
                                ]
                            },
                            "Attenuator": {
                                "inputs": [
                                    {
                                        "name": "INPUT",
                                        "type": "RandomMessage"
                                    }
                                ],
                                "upstreams": [
                                    "NoiseGenerator"
                                ]
                            },
                            "Sink": {
                                "inputs": [
                                    {
                                        "name": "INPUT_1",
                                        "type": "RandomMessage"
                                    },
                                    {
                                        "name": "INPUT_2",
                                        "type": "RandomMessage"
                                    },
                                    {
                                        "name": "INPUT_3",
                                        "type": "RandomMessage"
                                    }
                                ],
                                "upstreams": [
                                    "RollingAverager",
                                    "Amplifier",
                                    "Attenuator"
                                ]
                            }
                        }
                    },
                    "produced_timestamp_s": 1644347685.4051795,
                    "timestamp_s": 1644347685.4051795
                }
            ],
            "batch_num": 104
        }
    }
}

```

The above-serialized representation was generated for the following graph:
https://github.com/facebookresearch/labgraph/blob/main/extensions/graphviz_support/graphviz_support/tests/demo_graph/demo.py


3. To stop receiving data from the server, send the following `EndStreamRequest` to **ws://127.0.0.1:9000**

```
{
   "api_version": "0.1",
   "api_request": {
     "request_id": 1,
     "end_stream_request": {
       "stream_id": "LABGRAPH.MONITOR",
        "labgraph.monitor": {
        }
     }
   }
}
```

#### Labgraph YAML Parser:
**yamlify(python_file: str, yaml_file: str) -> str** : This function can be used to generate a YAMLIFIED version of the passed LabGraph source code(.py). The serialized version will be saved as a YAML file at the specified folder(yml_file)


1. Call **yamlify(python_file: str, yaml_file: str) -> str** and pass the appropriate parameters
```
from extensions.yaml_support.labgraph_yaml_parser.yamlify import (
    yamlify
)

yamlify(python_file, output_yaml_file)
```

This will generate a YAML file in the specified location

