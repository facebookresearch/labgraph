/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { useEffect, useState } from 'react';
import ReactFlow, {
    ReactFlowProvider,
    Controls,
    Background,
    Edge,
    Node,
    isNode,
    isEdge,
} from 'react-flow-renderer';
import { TGraphElement } from './types/TGraphElement';
import { useUIContext } from '../../contexts';
import { layoutGraph } from './util/layoutGraph';
import { RootState } from '../../redux/store';
import { useSelector, useDispatch } from 'react-redux';
import {
    setPanel,
    setTabIndex,
    setSelectedNode,
    setSelectedEdge,
} from '../../redux/reducers/config/configReducer';
import WS_STATE from '../../redux/reducers/graph/ws/enums/WS_STATE';
import { Box } from '@mui/material';

/**
 * A component that represents LabGraph computational graph.
 *
 * @returns {JSX.Element}
 */
const Graph: React.FC = (): JSX.Element => {
    const { layout } = useUIContext();
    const { mockGraph } = useSelector((state: RootState) => state.mock);

    const { connection, graph: realtimeGraph } = useSelector(
        (state: RootState) => state.ws
    );

    const serializedGraph =
        connection === WS_STATE.CONNECTED ? realtimeGraph : mockGraph;

    const [graph, setGraph] = useState<Array<TGraphElement>>(
        [] as Array<TGraphElement>
    );

    const dispatch = useDispatch();

    useEffect(() => {
        const { nodes } = serializedGraph;
        const deserializedGraph = [] as Array<TGraphElement>;
        if (!nodes) return;
        for (const [name, data] of Object.entries(nodes)) {
            deserializedGraph.push({
                id: name,
                data: {
                    label: name,
                },
                position: { x: 0, y: 0 },
                targetPosition: layout === 'horizontal' ? 'left' : 'top',
                sourcePosition: layout === 'horizontal' ? 'right' : 'bottom',
                style: {
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    width: '150px',
                    height: '150px',
                    borderRadius: '50%',
                    fontWeight: '500',
                    fill: 'currentColor',
                },
            });

            Object.entries(data.upstreams).forEach(([upstream, messages]) => {
                messages.forEach((message) => {
                    deserializedGraph.push({
                        id: `e${upstream}-${name}`,
                        label: `${message.name}`,
                        source: upstream,
                        target: name,
                        arrowHeadType: 'arrow',
                        type: 'default',
                        animated: Object.keys(nodes[upstream].upstreams).length
                            ? false
                            : true,
                        style: {
                            stroke: 'currentColor',
                        },
                    });
                });
            });
        }
        setGraph(layoutGraph(deserializedGraph, layout));
    }, [serializedGraph, layout]);

    const handleElementClick = (
        event: React.MouseEvent<Element, MouseEvent>,
        element: Node | Edge
    ) => {
        if (isNode(element)) {
            dispatch(setPanel(true));
            dispatch(setTabIndex('2'));
            dispatch(setSelectedNode(element));
        } else if (isEdge(element)) {
            dispatch(setPanel(true));
            dispatch(setTabIndex('3'));
            dispatch(setSelectedEdge(element));
        }
    };

    return (
        <Box data-testid="graph">
            <ReactFlowProvider>
                <ReactFlow
                    elements={graph as any}
                    style={{ width: '100%', height: '100vh' }}
                    onElementClick={handleElementClick}
                >
                    <Controls
                        showZoom={false}
                        showInteractive={false}
                        showFitView={true}
                        style={{
                            position: 'absolute',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            bottom: '40px',
                            left: '40px',
                            cursor: 'pointer',
                        }}
                    />
                    <Background size={0} />
                </ReactFlow>
            </ReactFlowProvider>
        </Box>
    );
};

export default Graph;
