# YAML Support | LabGraph Monitor

**This extension provides an API to generate a serialized version of the graph topology.** 

The serialized graph topology can be used in different applications. But it was specifically designed to work with server-client communications, such as working in sync with [LabGraph Monitor Front-End](https://github.com/facebookresearch/labgraph/tree/main/extensions/prototypes/labgraph_monitor) to get a simplified overview of the topology, along with real-time messaging, in case of complicated graphs.


## Quick Start

### Prerequisites:

- Python3\
  Supported python version(s)
  - [Python3.6](https://www.python.org/downloads/)
  - [Python3.8](https://www.python.org/downloads/) (**RECOMMENDED**)
- [LabGraph](https://github.com/facebookresearch/labgraph)

```bash
cd labgraph/extensions/yaml_support
python setup.py install
```

### Testing:

To make sure things are working:

1- Move to the root of the LabGraph directory:

```bash
labgraph\extensions\yaml_support> cd ../..
labgraph>
```

2- Run the following tests

```bash
python -m extensions.yaml_support.labgraph_monitor.tests.test_lg_monitor_api

python -m extensions.yaml_support.labgraph_yaml_parser.tests.test_lg_yaml_api
```

### LabGraph Monitor API:

#### Stream Graph Topology Only:

 - **`LabgraphMonitor(graph: lg.Graph)`** : This class serves as a facade for monitor's functions, 
 such as sending either topology or topology + real-time messages
 - **`stream_graph_topology() -> None`**: This function is used to send the generated serialized version of the graph instance via LabGraph WebSockets API

The serialized version of the graph will be streamed to the clients using LabGraph's [WebSockets API](https://github.com/facebookresearch/labgraph/blob/main/docs/websockets-api.md).

1. Instantiate a monitor object with **`LabgraphMonitor(graph: lg.Graph)`** to serialize your graph and stream via WebSockets API using its method **`stream_graph_topology() -> None`**

```python
from extensions.graphviz_support.graphviz_support.tests.demo_graph.demo import Demo

from extensions.yaml_support.labgraph_monitor.labgraph_monitor import LabgraphMonitor


# Initialize a Demo graph
graph = Demo()

# Initialize a monitor object
monitor = LabgraphMonitor(graph)

# Run the WebSockets API to send the topology to Front-End
monitor.stream_graph_topology()
```

This will start a websocket server on localhost port 9000 (127.0.0.1:9000)

2. To start receiving data from the server, send the following `StartStreamRequest` to **ws://127.0.0.1:9000**

```bash
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

```python
{
    name: "graph_name",
    nodes: {
        "node_name":{
            upstreams:{
                "upstream_name":[
                    {
                        name: "message_name",
                        fields: {
                            "timestamp": {
                                "type": "float",
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
}
```

An example of a single WebSockets API message 

```python
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
[`extensions/graphviz_support/graphviz_support/tests/demo_graph/demo.py`](https://github.com/facebookresearch/labgraph/blob/main/extensions/graphviz_support/graphviz_support/tests/demo_graph/demo.py
)

3. To stop receiving data from the server, send the following `EndStreamRequest` to **ws://127.0.0.1:9000**

```python
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

#### Stream Graph Topology AND Real-Time Messages:

This is used to stream both the graph topology and real-time messages received by nodes. However, it requires certain modifications to your graph outlined below:

1. Make sure that your graph is compatible with real-time messaging

 - It requires a `set_topology()` method to add attributes to your graph. This function is used by `generate_graph_topology(graph: lg.Graph) -> None` internally 

    ```python
    def set_topology(self, topology: SerializedGraph, sub_pub_map: Dict[str, str]) -> None:
        self._topology = topology
        self._sub_pub_match = sub_pub_map
    ```

- It also requires adding `WS_SERVER_NODE` and `SERIALIZER` nodes to your graph

    ```python
    self.WS_SERVER_NODE.configure(
        WSAPIServerConfig(
            app_id=APP_ID,
            ip=WS_SERVER.DEFAULT_IP,
            port=ENUMS.WS_SERVER.DEFAULT_PORT,
            api_version=ENUMS.WS_SERVER.DEFAULT_API_VERSION,
            num_messages=-1,
            enums=ENUMS(),
            sample_rate=SAMPLE_RATE,
        )
    )
    self.SERIALIZER.configure(
        SerializerConfig(
            data=self._topology,
            sub_pub_match=self._sub_pub_match,
            sample_rate=SAMPLE_RATE,
            stream_name=STREAM.LABGRAPH_MONITOR,
            stream_id=STREAM.LABGRAPH_MONITOR_ID,
        )
    )
    ```

 - As well as establishing connections between those nodes. Learn more in the example at [`yaml_support/labgraph_monitor/examples/labgraph_monitor_example.py`](https://github.com/facebookresearch/labgraph/blob/main/extensions/yaml_support/labgraph_monitor/examples/labgraph_monitor_example.py)

 2. You can then run your graph

    ```python
    from extensions.yaml_support.labgraph_monitor.examples.labgraph_monitor_example import Demo
    
    from extensions.yaml_support.labgraph_monitor.labgraph_monitor import LabgraphMonitor

    # Initialize a Demo graph
    graph = Demo()

    # Initialize a monitor object
    monitor = LabgraphMonitor(graph)

    # Run the WebSockets API to send the real-time topology to Front-End
    monitor.stream_real_time_graph()
    ```

3. Alternatively, you can simply run the example graph to try it out

    ```bash
    labgraph> python extensions/yaml_support/labgraph_monitor/examples/labgraph_monitor_example.py
    ```

4. To start receiving data from the server, send the following `StartStreamRequest` to **ws://127.0.0.1:9000**

    ```bash
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

The graph representation has the following schema:

```python
{
    name: "graph_name",
    nodes: {
        "node_name":{
            upstreams:{
                "upstream_name":[
                    {
                        name: "message_name",
                        fields: {
                            "timestamp": {
                                "type": "float",
                                "content": real-time value
                            },
                            "data": {
                                "type": "ndarray",
                                "content" real-time value
                            }
                        }
                    }
                ]
            }
        }
    }
}
```


<details> 

<summary>Click to see a full example of a serialized graph </summary>

```python

{
    "stream_batch": {
        "stream_id": "LABGRAPH.MONITOR",
        "labgraph.monitor": {
            "samples": [
                {
                    "data": {
                        "nodes": {
                            "WSAPIServerNode": {
                                "upstreams": {
                                    "Serializer": [
                                        {
                                            "name": "WSStreamMessage",
                                            "fields": {
                                                "samples": {
                                                    "type": "float64"
                                                },
                                                "stream_name": {
                                                    "type": "str"
                                                },
                                                "stream_id": {
                                                    "type": "str"
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            "Serializer": {
                                "upstreams": {
                                    "NoiseGenerator": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float",
                                                    "content": 1649542864.7681
                                                },
                                                "data": {
                                                    "type": "ndarray",
                                                    "content": [
                                                        0.6556638018597015,
                                                        0.24539091264180568,
                                                        0.5181571344277014,
                                                        0.15984381323928065,
                                                        0.3701566776459857,
                                                        0.7696829688461163,
                                                        0.5492927884621397,
                                                        0.21755380404615476,
                                                        0.175755558441702,
                                                        0.3505148522415169,
                                                        0.4350243443086518,
                                                        0.8366274099373696,
                                                        0.03302475842524499,
                                                        0.8704738525112928,
                                                        0.027029976451051985,
                                                        0.204213678026263,
                                                        0.27619466758117617,
                                                        0.0025992584637967164,
                                                        0.8518550799199274,
                                                        0.9698040142464401,
                                                        0.05805697223337192,
                                                        0.6698569790361546,
                                                        0.40671928409852365,
                                                        0.5008805646909648,
                                                        0.6510638383070676,
                                                        0.5260106707400308,
                                                        0.0582051587273289,
                                                        0.25106713695105276,
                                                        0.5142966826701221,
                                                        0.6819891025463702,
                                                        0.014206875156158705,
                                                        0.2535009607475609,
                                                        0.04284203715822765,
                                                        0.44622787715227075,
                                                        0.26505240918696915,
                                                        0.6723324403079721,
                                                        0.3993886748672555,
                                                        0.8619632017716233,
                                                        0.5675026279008025,
                                                        0.4411726561239213,
                                                        0.8971029120030483,
                                                        0.13464404361226445,
                                                        0.3257885658537706,
                                                        0.09289484114827451,
                                                        0.8086109528127211,
                                                        0.23881475974032784,
                                                        0.7182630487363211,
                                                        0.6471818603995376,
                                                        0.12258011209144437,
                                                        0.18605697048575598,
                                                        0.7339348679271822,
                                                        0.3363211275559638,
                                                        0.8530027602924856,
                                                        0.40234748928650654,
                                                        0.00039228723056528025,
                                                        0.691446585785186,
                                                        0.8633929722854425,
                                                        0.4511881940645861,
                                                        0.48228544914544236,
                                                        0.9744417858895236,
                                                        0.18154825917557527,
                                                        0.9753096692304941,
                                                        0.2717803735585991,
                                                        0.1053234497045098,
                                                        0.7827688514997935,
                                                        0.735434301027755,
                                                        0.7930935798860846,
                                                        0.9266795158135795,
                                                        0.7039903194866428,
                                                        0.11595408071998414,
                                                        0.7800548036145231,
                                                        0.5897624086470854,
                                                        0.2678583417730337,
                                                        0.3096243301685998,
                                                        0.21754492739103604,
                                                        0.37433310319419066,
                                                        0.008940695692322698,
                                                        0.5934725005680236,
                                                        0.024659685233431206,
                                                        0.006249709051017738,
                                                        0.5939358352718239,
                                                        0.9032715460908528,
                                                        0.5828267649749131,
                                                        0.4146803854885678,
                                                        0.8200852939412642,
                                                        0.7025396722944489,
                                                        0.356302414976882,
                                                        0.5966468416890455,
                                                        0.27785808269475387,
                                                        0.5186198788914278,
                                                        0.8821182046756642,
                                                        0.025102814974933163,
                                                        0.861080010979159,
                                                        0.8681611199938043,
                                                        0.483135709281621,
                                                        0.05159925273309407,
                                                        0.6374936766144756,
                                                        0.25726267728691266,
                                                        0.4150461824153807,
                                                        0.4038900091612285
                                                    ]
                                                }
                                            }
                                        }
                                    ],
                                    "RollingAverager": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float",
                                                    "content": 1649542864.778323
                                                },
                                                "data": {
                                                    "type": "ndarray",
                                                    "content": [
                                                        0.4808310849498126,
                                                        0.45765738986698584,
                                                        0.5179472617869983,
                                                        0.4545298437611365,
                                                        0.511475834694006,
                                                        0.6370143504941551,
                                                        0.5240116417975883,
                                                        0.6621674003277452,
                                                        0.39416145544465786,
                                                        0.626802455660307,
                                                        0.4379461617134113,
                                                        0.626555296204266,
                                                        0.5212543973073265,
                                                        0.5634172170782334,
                                                        0.6610150120658533,
                                                        0.5648671072511644,
                                                        0.36228861954728664,
                                                        0.40611552677263923,
                                                        0.528085032194146,
                                                        0.3795449315341961,
                                                        0.5564513831254658,
                                                        0.6020673565819801,
                                                        0.3920276747808733,
                                                        0.5398939864307285,
                                                        0.44071762995863917,
                                                        0.4685674882997472,
                                                        0.523320469875816,
                                                        0.4682660890981684,
                                                        0.4880738071953582,
                                                        0.6247477549472256,
                                                        0.37262642294916287,
                                                        0.5292429080330315,
                                                        0.3560642133686165,
                                                        0.42654180215294774,
                                                        0.48254525230183826,
                                                        0.474625466796003,
                                                        0.566613001586366,
                                                        0.6124545612880383,
                                                        0.521925508913315,
                                                        0.3644889004429638,
                                                        0.5516832937307365,
                                                        0.5487269330238846,
                                                        0.3776278084794831,
                                                        0.45893729288107465,
                                                        0.4358817754996432,
                                                        0.5017929922223582,
                                                        0.6077143546380854,
                                                        0.43706695205815843,
                                                        0.586934260076837,
                                                        0.5603784617106875,
                                                        0.5966846437692761,
                                                        0.38536876311879753,
                                                        0.5872066280396688,
                                                        0.2818328200671419,
                                                        0.5298252461922792,
                                                        0.47645896345478744,
                                                        0.6548108936817794,
                                                        0.4247103938231261,
                                                        0.5238473325787164,
                                                        0.42887801140492804,
                                                        0.5385221653828477,
                                                        0.4554488020724207,
                                                        0.5162366459311485,
                                                        0.47389905275366334,
                                                        0.4999364257892879,
                                                        0.5837869623887693,
                                                        0.5223744126545582,
                                                        0.4912632015305095,
                                                        0.45473824666589113,
                                                        0.49088925869540045,
                                                        0.5301869530654425,
                                                        0.6173096417477979,
                                                        0.4567178020980392,
                                                        0.47735235791449043,
                                                        0.4157221801958209,
                                                        0.4549033636138871,
                                                        0.46876329693604396,
                                                        0.4322555231630121,
                                                        0.5574453194471654,
                                                        0.5911688810594924,
                                                        0.5747328520895914,
                                                        0.5189652304462694,
                                                        0.5323873893686856,
                                                        0.40735471004222557,
                                                        0.5515387981684451,
                                                        0.38342621200700266,
                                                        0.438531088819206,
                                                        0.515587963010385,
                                                        0.32695685320343026,
                                                        0.5585212227871539,
                                                        0.6052757151735452,
                                                        0.5496641665985119,
                                                        0.5069727632398621,
                                                        0.5296129345037791,
                                                        0.5996831098341185,
                                                        0.4823400590757597,
                                                        0.44537321262358665,
                                                        0.46411654667438745,
                                                        0.5707572616456332,
                                                        0.5388152812937068
                                                    ]
                                                }
                                            }
                                        }
                                    ],
                                    "Amplifier": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float",
                                                    "content": 1649542864.7791843
                                                },
                                                "data": {
                                                    "type": "ndarray",
                                                    "content": [
                                                        0.7867965622316418,
                                                        0.2944690951701668,
                                                        0.6217885613132417,
                                                        0.19181257588713677,
                                                        0.4441880131751828,
                                                        0.9236195626153395,
                                                        0.6591513461545676,
                                                        0.2610645648553857,
                                                        0.21090667013004238,
                                                        0.4206178226898203,
                                                        0.5220292131703821,
                                                        1.0039528919248435,
                                                        0.03962971011029399,
                                                        1.0445686230135514,
                                                        0.03243597174126238,
                                                        0.2450564136315156,
                                                        0.3314336010974114,
                                                        0.00311911015655606,
                                                        1.022226095903913,
                                                        1.1637648170957282,
                                                        0.06966836668004629,
                                                        0.8038283748433855,
                                                        0.48806314091822833,
                                                        0.6010566776291577,
                                                        0.7812766059684811,
                                                        0.631212804888037,
                                                        0.06984619047279468,
                                                        0.3012805643412633,
                                                        0.6171560192041464,
                                                        0.8183869230556443,
                                                        0.017048250187390444,
                                                        0.30420115289707306,
                                                        0.051410444589873185,
                                                        0.5354734525827248,
                                                        0.31806289102436297,
                                                        0.8067989283695666,
                                                        0.47926640984070656,
                                                        1.034355842125948,
                                                        0.681003153480963,
                                                        0.5294071873487055,
                                                        1.076523494403658,
                                                        0.16157285233471733,
                                                        0.39094627902452467,
                                                        0.1114738093779294,
                                                        0.9703331433752653,
                                                        0.2865777116883934,
                                                        0.8619156584835853,
                                                        0.7766182324794452,
                                                        0.14709613450973325,
                                                        0.22326836458290716,
                                                        0.8807218415126187,
                                                        0.40358535306715654,
                                                        1.0236033123509827,
                                                        0.48281698714380783,
                                                        0.0004707446766783363,
                                                        0.8297359029422232,
                                                        1.036071566742531,
                                                        0.5414258328775033,
                                                        0.5787425389745308,
                                                        1.1693301430674283,
                                                        0.21785791101069032,
                                                        1.170371603076593,
                                                        0.3261364482703189,
                                                        0.12638813964541176,
                                                        0.9393226217997521,
                                                        0.8825211612333059,
                                                        0.9517122958633015,
                                                        1.1120154189762954,
                                                        0.8447883833839713,
                                                        0.13914489686398096,
                                                        0.9360657643374276,
                                                        0.7077148903765025,
                                                        0.32143001012764044,
                                                        0.37154919620231974,
                                                        0.26105391286924323,
                                                        0.4491997238330288,
                                                        0.010728834830787237,
                                                        0.7121670006816283,
                                                        0.029591622280117445,
                                                        0.007499650861221285,
                                                        0.7127230023261887,
                                                        1.0839258553090234,
                                                        0.6993921179698958,
                                                        0.49761646258628134,
                                                        0.984102352729517,
                                                        0.8430476067533387,
                                                        0.4275628979722584,
                                                        0.7159762100268545,
                                                        0.33342969923370464,
                                                        0.6223438546697133,
                                                        1.058541845610797,
                                                        0.030123377969919794,
                                                        1.0332960131749906,
                                                        1.041793343992565,
                                                        0.5797628511379451,
                                                        0.06191910327971288,
                                                        0.7649924119373708,
                                                        0.3087152127442952,
                                                        0.49805541889845684,
                                                        0.48466801099347423
                                                    ]
                                                }
                                            }
                                        }
                                    ],
                                    "Attenuator": [
                                        {
                                            "name": "RandomMessage",
                                            "fields": {
                                                "timestamp": {
                                                    "type": "float",
                                                    "content": 1649542864.7761025
                                                },
                                                "data": {
                                                    "type": "ndarray",
                                                    "content": [
                                                        1.1659534387549473,
                                                        0.43637360736158304,
                                                        0.9214281633175516,
                                                        0.28424696190551973,
                                                        0.6582419983462712,
                                                        1.3687113757566782,
                                                        0.9767960558050885,
                                                        0.3868714503109195,
                                                        0.3125424907767712,
                                                        0.6233133446539249,
                                                        0.7735948343497585,
                                                        1.4877572969658177,
                                                        0.05872724792912261,
                                                        1.54794572889809,
                                                        0.048066850576742697,
                                                        0.3631489788824215,
                                                        0.49115129052215034,
                                                        0.004622207807539101,
                                                        1.5148363489586678,
                                                        1.7245825103075385,
                                                        0.10324151833180674,
                                                        1.191192873490868,
                                                        0.7232605285781757,
                                                        0.8907055950786112,
                                                        1.1577734182823687,
                                                        0.9353939452377601,
                                                        0.10350503532285629,
                                                        0.44646752017747954,
                                                        0.9145632014435997,
                                                        1.2127671789291337,
                                                        0.02526379357119053,
                                                        0.4507955389224727,
                                                        0.07618511256259868,
                                                        0.7935178461252609,
                                                        0.47133724183839865,
                                                        1.19559493530089,
                                                        0.7102246571191703,
                                                        1.5328114139217033,
                                                        1.0091782383389774,
                                                        0.7845282506573513,
                                                        1.5952996371009802,
                                                        0.23943473044007263,
                                                        0.5793430986838699,
                                                        0.16519298331281304,
                                                        1.437936208118817,
                                                        0.42467937005961726,
                                                        1.277272390559583,
                                                        1.1508701768991823,
                                                        0.21798168941247872,
                                                        0.3308612797090394,
                                                        1.3051412639445443,
                                                        0.5980729362938445,
                                                        1.5168772453344939,
                                                        0.7154862558790507,
                                                        0.0006975963049354294,
                                                        1.2295852266435081,
                                                        1.5353539453875087,
                                                        0.8023386755576991,
                                                        0.8576382839767142,
                                                        1.7328297641288963,
                                                        0.32284353122033543,
                                                        1.73437310320446,
                                                        0.4833014423519436,
                                                        0.18729452200379984,
                                                        1.3919817314418979,
                                                        1.3078076749540237,
                                                        1.4103419833454838,
                                                        1.6478951026761268,
                                                        1.25189149000982,
                                                        0.20619875425433903,
                                                        1.3871553959696619,
                                                        1.0487623481120731,
                                                        0.4763269739821545,
                                                        0.5505985711859143,
                                                        0.3868556651378918,
                                                        0.6656688499062046,
                                                        0.015899055061081146,
                                                        1.0553599281844293,
                                                        0.04385181050865158,
                                                        0.011113728924158739,
                                                        1.0561838667481538,
                                                        1.6062691920873873,
                                                        1.0364288357744824,
                                                        0.7374175912613233,
                                                        1.4583407926914678,
                                                        1.2493118339767106,
                                                        0.6336052483005331,
                                                        1.0610047936403824,
                                                        0.4941093073689731,
                                                        0.9222510522695058,
                                                        1.5686526405952337,
                                                        0.04463981900394038,
                                                        1.531240853920328,
                                                        1.5438330442813126,
                                                        0.8591502840700574,
                                                        0.0917578887086558,
                                                        1.1336418791535336,
                                                        0.4574849219908048,
                                                        0.7380680804045303,
                                                        0.7182292872118445
                                                    ]
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
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
                                                    "type": "float",
                                                    "content": 1649542864.7681
                                                },
                                                "data": {
                                                    "type": "ndarray",
                                                    "content": [
                                                        0.6556638018597015,
                                                        0.24539091264180568,
                                                        0.5181571344277014,
                                                        0.15984381323928065,
                                                        0.3701566776459857,
                                                        0.7696829688461163,
                                                        0.5492927884621397,
                                                        0.21755380404615476,
                                                        0.175755558441702,
                                                        0.3505148522415169,
                                                        0.4350243443086518,
                                                        0.8366274099373696,
                                                        0.03302475842524499,
                                                        0.8704738525112928,
                                                        0.027029976451051985,
                                                        0.204213678026263,
                                                        0.27619466758117617,
                                                        0.0025992584637967164,
                                                        0.8518550799199274,
                                                        0.9698040142464401,
                                                        0.05805697223337192,
                                                        0.6698569790361546,
                                                        0.40671928409852365,
                                                        0.5008805646909648,
                                                        0.6510638383070676,
                                                        0.5260106707400308,
                                                        0.0582051587273289,
                                                        0.25106713695105276,
                                                        0.5142966826701221,
                                                        0.6819891025463702,
                                                        0.014206875156158705,
                                                        0.2535009607475609,
                                                        0.04284203715822765,
                                                        0.44622787715227075,
                                                        0.26505240918696915,
                                                        0.6723324403079721,
                                                        0.3993886748672555,
                                                        0.8619632017716233,
                                                        0.5675026279008025,
                                                        0.4411726561239213,
                                                        0.8971029120030483,
                                                        0.13464404361226445,
                                                        0.3257885658537706,
                                                        0.09289484114827451,
                                                        0.8086109528127211,
                                                        0.23881475974032784,
                                                        0.7182630487363211,
                                                        0.6471818603995376,
                                                        0.12258011209144437,
                                                        0.18605697048575598,
                                                        0.7339348679271822,
                                                        0.3363211275559638,
                                                        0.8530027602924856,
                                                        0.40234748928650654,
                                                        0.00039228723056528025,
                                                        0.691446585785186,
                                                        0.8633929722854425,
                                                        0.4511881940645861,
                                                        0.48228544914544236,
                                                        0.9744417858895236,
                                                        0.18154825917557527,
                                                        0.9753096692304941,
                                                        0.2717803735585991,
                                                        0.1053234497045098,
                                                        0.7827688514997935,
                                                        0.735434301027755,
                                                        0.7930935798860846,
                                                        0.9266795158135795,
                                                        0.7039903194866428,
                                                        0.11595408071998414,
                                                        0.7800548036145231,
                                                        0.5897624086470854,
                                                        0.2678583417730337,
                                                        0.3096243301685998,
                                                        0.21754492739103604,
                                                        0.37433310319419066,
                                                        0.008940695692322698,
                                                        0.5934725005680236,
                                                        0.024659685233431206,
                                                        0.006249709051017738,
                                                        0.5939358352718239,
                                                        0.9032715460908528,
                                                        0.5828267649749131,
                                                        0.4146803854885678,
                                                        0.8200852939412642,
                                                        0.7025396722944489,
                                                        0.356302414976882,
                                                        0.5966468416890455,
                                                        0.27785808269475387,
                                                        0.5186198788914278,
                                                        0.8821182046756642,
                                                        0.025102814974933163,
                                                        0.861080010979159,
                                                        0.8681611199938043,
                                                        0.483135709281621,
                                                        0.05159925273309407,
                                                        0.6374936766144756,
                                                        0.25726267728691266,
                                                        0.4150461824153807,
                                                        0.4038900091612285
                                                    ]
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
                                                    "type": "float",
                                                    "content": 1649542864.7681
                                                },
                                                "data": {
                                                    "type": "ndarray",
                                                    "content": [
                                                        0.6556638018597015,
                                                        0.24539091264180568,
                                                        0.5181571344277014,
                                                        0.15984381323928065,
                                                        0.3701566776459857,
                                                        0.7696829688461163,
                                                        0.5492927884621397,
                                                        0.21755380404615476,
                                                        0.175755558441702,
                                                        0.3505148522415169,
                                                        0.4350243443086518,
                                                        0.8366274099373696,
                                                        0.03302475842524499,
                                                        0.8704738525112928,
                                                        0.027029976451051985,
                                                        0.204213678026263,
                                                        0.27619466758117617,
                                                        0.0025992584637967164,
                                                        0.8518550799199274,
                                                        0.9698040142464401,
                                                        0.05805697223337192,
                                                        0.6698569790361546,
                                                        0.40671928409852365,
                                                        0.5008805646909648,
                                                        0.6510638383070676,
                                                        0.5260106707400308,
                                                        0.0582051587273289,
                                                        0.25106713695105276,
                                                        0.5142966826701221,
                                                        0.6819891025463702,
                                                        0.014206875156158705,
                                                        0.2535009607475609,
                                                        0.04284203715822765,
                                                        0.44622787715227075,
                                                        0.26505240918696915,
                                                        0.6723324403079721,
                                                        0.3993886748672555,
                                                        0.8619632017716233,
                                                        0.5675026279008025,
                                                        0.4411726561239213,
                                                        0.8971029120030483,
                                                        0.13464404361226445,
                                                        0.3257885658537706,
                                                        0.09289484114827451,
                                                        0.8086109528127211,
                                                        0.23881475974032784,
                                                        0.7182630487363211,
                                                        0.6471818603995376,
                                                        0.12258011209144437,
                                                        0.18605697048575598,
                                                        0.7339348679271822,
                                                        0.3363211275559638,
                                                        0.8530027602924856,
                                                        0.40234748928650654,
                                                        0.00039228723056528025,
                                                        0.691446585785186,
                                                        0.8633929722854425,
                                                        0.4511881940645861,
                                                        0.48228544914544236,
                                                        0.9744417858895236,
                                                        0.18154825917557527,
                                                        0.9753096692304941,
                                                        0.2717803735585991,
                                                        0.1053234497045098,
                                                        0.7827688514997935,
                                                        0.735434301027755,
                                                        0.7930935798860846,
                                                        0.9266795158135795,
                                                        0.7039903194866428,
                                                        0.11595408071998414,
                                                        0.7800548036145231,
                                                        0.5897624086470854,
                                                        0.2678583417730337,
                                                        0.3096243301685998,
                                                        0.21754492739103604,
                                                        0.37433310319419066,
                                                        0.008940695692322698,
                                                        0.5934725005680236,
                                                        0.024659685233431206,
                                                        0.006249709051017738,
                                                        0.5939358352718239,
                                                        0.9032715460908528,
                                                        0.5828267649749131,
                                                        0.4146803854885678,
                                                        0.8200852939412642,
                                                        0.7025396722944489,
                                                        0.356302414976882,
                                                        0.5966468416890455,
                                                        0.27785808269475387,
                                                        0.5186198788914278,
                                                        0.8821182046756642,
                                                        0.025102814974933163,
                                                        0.861080010979159,
                                                        0.8681611199938043,
                                                        0.483135709281621,
                                                        0.05159925273309407,
                                                        0.6374936766144756,
                                                        0.25726267728691266,
                                                        0.4150461824153807,
                                                        0.4038900091612285
                                                    ]
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
                                                    "type": "float",
                                                    "content": 1649542864.7681
                                                },
                                                "data": {
                                                    "type": "ndarray",
                                                    "content": [
                                                        0.6556638018597015,
                                                        0.24539091264180568,
                                                        0.5181571344277014,
                                                        0.15984381323928065,
                                                        0.3701566776459857,
                                                        0.7696829688461163,
                                                        0.5492927884621397,
                                                        0.21755380404615476,
                                                        0.175755558441702,
                                                        0.3505148522415169,
                                                        0.4350243443086518,
                                                        0.8366274099373696,
                                                        0.03302475842524499,
                                                        0.8704738525112928,
                                                        0.027029976451051985,
                                                        0.204213678026263,
                                                        0.27619466758117617,
                                                        0.0025992584637967164,
                                                        0.8518550799199274,
                                                        0.9698040142464401,
                                                        0.05805697223337192,
                                                        0.6698569790361546,
                                                        0.40671928409852365,
                                                        0.5008805646909648,
                                                        0.6510638383070676,
                                                        0.5260106707400308,
                                                        0.0582051587273289,
                                                        0.25106713695105276,
                                                        0.5142966826701221,
                                                        0.6819891025463702,
                                                        0.014206875156158705,
                                                        0.2535009607475609,
                                                        0.04284203715822765,
                                                        0.44622787715227075,
                                                        0.26505240918696915,
                                                        0.6723324403079721,
                                                        0.3993886748672555,
                                                        0.8619632017716233,
                                                        0.5675026279008025,
                                                        0.4411726561239213,
                                                        0.8971029120030483,
                                                        0.13464404361226445,
                                                        0.3257885658537706,
                                                        0.09289484114827451,
                                                        0.8086109528127211,
                                                        0.23881475974032784,
                                                        0.7182630487363211,
                                                        0.6471818603995376,
                                                        0.12258011209144437,
                                                        0.18605697048575598,
                                                        0.7339348679271822,
                                                        0.3363211275559638,
                                                        0.8530027602924856,
                                                        0.40234748928650654,
                                                        0.00039228723056528025,
                                                        0.691446585785186,
                                                        0.8633929722854425,
                                                        0.4511881940645861,
                                                        0.48228544914544236,
                                                        0.9744417858895236,
                                                        0.18154825917557527,
                                                        0.9753096692304941,
                                                        0.2717803735585991,
                                                        0.1053234497045098,
                                                        0.7827688514997935,
                                                        0.735434301027755,
                                                        0.7930935798860846,
                                                        0.9266795158135795,
                                                        0.7039903194866428,
                                                        0.11595408071998414,
                                                        0.7800548036145231,
                                                        0.5897624086470854,
                                                        0.2678583417730337,
                                                        0.3096243301685998,
                                                        0.21754492739103604,
                                                        0.37433310319419066,
                                                        0.008940695692322698,
                                                        0.5934725005680236,
                                                        0.024659685233431206,
                                                        0.006249709051017738,
                                                        0.5939358352718239,
                                                        0.9032715460908528,
                                                        0.5828267649749131,
                                                        0.4146803854885678,
                                                        0.8200852939412642,
                                                        0.7025396722944489,
                                                        0.356302414976882,
                                                        0.5966468416890455,
                                                        0.27785808269475387,
                                                        0.5186198788914278,
                                                        0.8821182046756642,
                                                        0.025102814974933163,
                                                        0.861080010979159,
                                                        0.8681611199938043,
                                                        0.483135709281621,
                                                        0.05159925273309407,
                                                        0.6374936766144756,
                                                        0.25726267728691266,
                                                        0.4150461824153807,
                                                        0.4038900091612285
                                                    ]
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "produced_timestamp_s": 1649542864.9706066,
                    "timestamp_s": 1649542864.9706097
                }
            ],
            "batch_num": 53
        }
    }
}

```

</details>

3. To stop receiving data from the server, send the following `EndStreamRequest` to **ws://127.0.0.1:9000**

```python
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

# LabGraph YAML Parser:

**`yamlify(python_file: str, yaml_file: str) -> str`** : This function can be used to generate a YAMLIFIED version of the passed LabGraph source code (.py). The serialized version will be saved as a YAML file at the specified folder (yml_file)

1. Call **yamlify(python_file: str, yaml_file: str) -> str** and pass the appropriate parameters

```python
from extensions.yaml_support.labgraph_yaml_parser.yamlify import (
    yamlify
)

yamlify(python_file, output_yaml_file)
```

This will generate a YAML file in the specified location

Example of a YAML file produced for [`simple_viz.py`](https://github.com/facebookresearch/labgraph/blob/main/labgraph/examples/simple_viz.py) example:

```python
RandomMessage:
  type: Message
  fields:
    timestamp: float
    data: np.ndarray

NoiseGeneratorConfig:
  type: Config
  fields:
    sample_rate: float
    num_features: int

NoiseGenerator:
  type: Node
  config: NoiseGeneratorConfig
  inputs: []
  outputs:
  - RandomMessage

RollingState:
  type: State
  fields:
    messages: List.RandomMessage

RollingConfig:
  type: Config
  fields:
    window: float

RollingAverager:
  type: Node
  state: RollingState
  config: RollingConfig
  inputs:
  - RandomMessage
  outputs:
  - RandomMessage

AveragedNoiseConfig:
  type: Config
  fields:
    sample_rate: float
    num_features: int
    window: float

AveragedNoise:
  type: Group
  config: AveragedNoiseConfig
  inputs: []
  outputs:
  - RandomMessage
  connections:
    NoiseGenerator: RollingAverager
    RollingAverager: AveragedNoise

PlotState:
  type: State
  fields:
    data: Optional.np.ndarray

PlotConfig:
  type: Config
  fields:
    refresh_rate: float
    num_bars: int

Plot:
  type: Node
  state: PlotState
  config: PlotConfig
  inputs:
  - RandomMessage
  outputs: []

Demo:
  type: Graph
  inputs: []
  outputs: []
  connections:
    AveragedNoise: Plot
```
