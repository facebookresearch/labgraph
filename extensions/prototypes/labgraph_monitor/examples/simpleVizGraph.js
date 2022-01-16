/**

Copyright (c) Facebook, Inc. and its affiliates.
This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
*/

import React, { useState, useEffect, useCallback} from 'react';
import ReactFlow, { addEdge, MiniMap, Controls, Background, isNode} from 'react-flow-renderer';
import { dataToConnections, connectionsToNodes, dataToObjects } from './helper';
import './App.css';
import dagre from 'dagre';

const data = [
    [
        {
            "NoiseGenerator": {
                "type": "Node",
                "config": {
                    "NoiseGeneratorConfig": {
                        "sample_rate": "float",
                        "num_features": "int"
                    }
                },
                "inputs": [],
                "outputs": [
                    {
                        "RandomMessage": {
                            "timestamp": "float",
                            "data": "np.ndarray"
                        }
                    }
                ]
            }
        },
        {
            "RollingAverager": {
                "type": "Node",
                "state": {
                    "RollingState": {
                        "messages": "List.RandomMessage"
                    }
                },
                "config": {
                    "RollingConfig": {
                        "window": "float"
                    }
                },
                "inputs": [
                    {
                        "RandomMessage": {
                            "timestamp": "float",
                            "data": "np.ndarray"
                        }
                    }
                ],
                "outputs": [
                    {
                        "RandomMessage": {
                            "timestamp": "float",
                            "data": "np.ndarray"
                        }
                    }
                ]
            }
        }
    ],
    [
        {
            "RollingAverager": {
                "type": "Node",
                "state": {
                    "RollingState": {
                        "messages": "List.RandomMessage"
                    }
                },
                "config": {
                    "RollingConfig": {
                        "window": "float"
                    }
                },
                "inputs": [
                    {
                        "RandomMessage": {
                            "timestamp": "float",
                            "data": "np.ndarray"
                        }
                    }
                ],
                "outputs": [
                    {
                        "RandomMessage": {
                            "timestamp": "float",
                            "data": "np.ndarray"
                        }
                    }
                ]
            }
        },
        {
            "AveragedNoise": {
                "type": "Group",
                "config": {
                    "AveragedNoiseConfig": {
                        "sample_rate": "float",
                        "num_features": "int",
                        "window": "float"
                    }
                },
                "inputs": [],
                "outputs": [
                    {
                        "RandomMessage": {
                            "timestamp": "float",
                            "data": "np.ndarray"
                        }
                    }
                ],
                "connections": {
                    "NoiseGenerator": "RollingAverager",
                    "RollingAverager": "AveragedNoise"
                }
            }
        }
    ],
    [
        {
            "AveragedNoise": {
                "type": "Group",
                "config": {
                    "AveragedNoiseConfig": {
                        "sample_rate": "float",
                        "num_features": "int",
                        "window": "float"
                    }
                },
                "inputs": [],
                "outputs": [
                    {
                        "RandomMessage": {
                            "timestamp": "float",
                            "data": "np.ndarray"
                        }
                    }
                ],
                "connections": {
                    "NoiseGenerator": "RollingAverager",
                    "RollingAverager": "AveragedNoise"
                }
            }
        },
        {
            "Plot": {
                "type": "Node",
                "state": "PlotState",
                "config": "PlotConfig",
                "inputs": [
                    "RandomMessage"
                ],
                "outputs": []
            }
        }
    ]
]

// dagreGraph helps layout the nodes in the graph 
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172;
const nodeHeight = 36;

// setting up the horizontal and vertical options to change the orientation 
const getLayoutedElements = (elements, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  elements.forEach((el) => {
    if (isNode(el)) {
      dagreGraph.setNode(el.id, { width: nodeWidth, height: nodeHeight });
    } else {
      dagreGraph.setEdge(el.source, el.target);
    }
  });

  dagre.layout(dagreGraph);

  return elements.map((el) => {
    if (isNode(el)) {
      const nodeWithPosition = dagreGraph.node(el.id);
      el.targetPosition = isHorizontal ? 'left' : 'top';
      el.sourcePosition = isHorizontal ? 'right' : 'bottom';
      el.position = {
        x: nodeWithPosition.x - nodeWidth / 2 + Math.random() / 1000,
        y: nodeWithPosition.y - nodeHeight / 2,
      };
    }

    return el;
  });
};

const InteractionGraph = () => {
  const [node_name, setName] = useState("None");
  const [connections, setConnections] = useState([]);
  const [elements, setElements] = useState([]);
  const [nodeObjects, setNodeObjects] = useState([]);
  const [type, setType] = useState('None')

  // getting the node that the user is clicking 
  const onElementClick = (event, element) => {
    setName(element.id)
    setType(nodeObjects[element.id].type)
    console.log("node", node_name)
  };

  // receiving the messages from server 
  useEffect(() => {
        const connections = dataToConnections(data); // generating the connections array 
        const elements = connectionsToNodes(connections); // changing the connections array to an elements array having the properties of nodes in reactflow
        const layoutedElements = getLayoutedElements(elements); // using dagreGraph and the getLayoutedElements function defined earlier to layout the nodes
        const nodeObjects = dataToObjects(data); 
        setElements(layoutedElements);
        setConnections(connections);
        setNodeObjects(nodeObjects);
        console.log("nodeObjects", nodeObjects);
        console.log("connection", connections);
        console.log("server message received ", data)

    return () => {
    }
  }, []);

  const onLayout = useCallback(
    (direction) => {
      const layoutedElements = getLayoutedElements(elements, direction);
      setElements(layoutedElements);
    },
    [elements]
  );

  return(
  <div>
    <div className='table-div'> 
      <div className='annotations'></div>
      <div className="controls">
          <button onClick={() => onLayout('TB')}>vertical layout</button>
          <button onClick={() => onLayout('LR')}>horizontal layout</button>
        </div>
      <table>
        <thead>
          <tr>
            <th>Node</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>{node_name}</td>
            <td>{type}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div style={{ height: 400 }}> 
    <ReactFlow 
    elements={elements}
    onElementClick={onElementClick}
    >
      <MiniMap
        nodeBorderRadius={2}
      />
      <Controls />
      <Background color="#aaa" gap={16} />
    </ReactFlow>
    </div>

  </div>

  
  )
};

export default InteractionGraph;