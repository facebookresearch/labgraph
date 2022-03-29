# YAML Support for LabGraph

This extension provides an API to generate a serialized version of the labgraph topology. The serialized graph topology can be used in different applications E.g: server-client communication or to get a simplified overview of the topology in case of complicated graphs.

## Quick Start

### Method 1 - building from source code

**Prerequisites**:

- Python3\
  Supported python version(s)
  _ [Python3.6](https://www.python.org/downloads/)
  _ [Python3.8](https://www.python.org/downloads/) (**RECOMMENDED**)
- Make sure to install [labgraph](https://github.com/facebookresearch/labgraph) before proceeding

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

**generate_graph_topology(graph: lg.Graph) -> SerializedGraph** : This function can be used to generate a serialized version of the passed graph instance. 
**run_topology(data: SerializedGraph) -> None**: This function can be used to send the generated serialized version of the graph instance via LabGraph Websockets API.

The serialized version of the graph will be streamed to the clients using LabGraph Websockets API.

1. Call **generate_graph_topology(graph: lg.Graph) -> SerializedGraph** and pass an instance of the graph as a parameter

```
from extensions.graphviz_support.graphviz_support.tests.demo_graph.demo import Demo

from extensions.yaml_support.labgraph_monitor.generate_lg_monitor.generate_lg_monitor import (
    generate_graph_topology,
)

from extensions.yaml_support.labgraph_monitor.server.lg_monitor_server import (
    run_topology,
)

# Initialize a Demo graph
graph = Demo()

# Serialize its topology
topology = generate_graph_topology(graph)

# Run the WebSockets API to send the topology to Front-End
run_topology(topology)
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
```

E.g:

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
                                "upstreams": {}
                            },
                            "RollingAverager": {
                                "upstreams": {
                                    "NoiseGenerator": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float"
                                                },
                                                "data": {
                                                    "type": "ndarray"
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            "Amplifier": {
                                "upstreams": {
                                    "NoiseGenerator": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float"
                                                },
                                                "data": {
                                                    "type": "ndarray"
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            "Attenuator": {
                                "upstreams": {
                                    "NoiseGenerator": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float"
                                                },
                                                "data": {
                                                    "type": "ndarray"
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            "Sink": {
                                "upstreams": {
                                    "RollingAverager": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float"
                                                },
                                                "data": {
                                                    "type": "ndarray"
                                                }
                                            }
                                        }
                                    ],
                                    "Amplifier": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float"
                                                },
                                                "data": {
                                                    "type": "ndarray"
                                                }
                                            }
                                        }
                                    ],
                                    "Attenuator": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float"
                                                },
                                                "data": {
                                                    "type": "ndarray"
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "produced_timestamp_s": 1648581339.9652574,
                    "timestamp_s": 1648581339.965258
                }
            ],
            "batch_num": 31
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
