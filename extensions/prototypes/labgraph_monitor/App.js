import React, { useState, useEffect, useCallback} from 'react';
import { w3cwebsocket as W3CWebSocket } from "websocket";
import ReactFlow, { addEdge, MiniMap, Controls, Background, isNode} from 'react-flow-renderer';
import { dataToConnections, connectionsToNodes, dataToObjects } from './helper';
import './App.css';
import dagre from 'dagre';

// sample connections array: {'NoiseGenerator': ['RollingAverager'], 'RollingAverager': ['AveragedNoise'], 'AveragedNoise': ['Plot']}

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
    // connecting to the server 
    const client = new W3CWebSocket('ws://localhost:9000');

    client.onopen = () => {
      console.log('connected');
      client.send(JSON.stringify({
        "api_version": "0.1",
        "api_request": {
          "request_id": 1,
          "start_stream_request": {
            "stream_id": "LABGRAPH.MONITOR",
             "labgraph.monitor": {
             }
          }
        }
     }))
    };

    client.onmessage = (message) => {
      const dataFromServer = JSON.parse(message.data);
      if (dataFromServer.stream_batch){
        const dataArray = dataFromServer.stream_batch["labgraph.monitor"].samples[0].data; // dataArray is the part of JSON data we are interested in
        const connections = dataToConnections(dataArray); // generating the connections array 
        const elements = connectionsToNodes(connections); // changing the connections array to an elements array having the properties of nodes in reactflow
        const layoutedElements = getLayoutedElements(elements); // using dagreGraph and the getLayoutedElements function defined earlier to layout the nodes
        const nodeObjects = dataToObjects(dataArray); 
        setElements(layoutedElements);
        setConnections(connections);
        setNodeObjects(nodeObjects);
        console.log("nodeObjects", nodeObjects);
        console.log("connection", connections);
        console.log("server message received ", dataArray)
      }
    };

    return () => {
      client.close();
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