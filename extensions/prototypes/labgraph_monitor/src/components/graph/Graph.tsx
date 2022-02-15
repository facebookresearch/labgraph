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
import { useWSContext, useUIContext, useConfigContext } from '../../contexts';
import { layoutGraph } from './util/layoutGraph';

const Graph: React.FC = (): JSX.Element => {
    const { layout } = useUIContext();
    const { setPanel, setSelectedNode, setSelectedEdge } = useConfigContext();
    const { graph: serializedGraph } = useWSContext();
    const [graph, setGraph] = useState<Array<TGraphElement>>(
        [] as Array<TGraphElement>
    );

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
            setPanel({
                isOpen: true,
                panelIndex: '2',
            });

            setSelectedNode(element);
        } else if (isEdge(element)) {
            setPanel({
                isOpen: true,
                panelIndex: '3',
            });

            setSelectedEdge(element);
        }
    };

    return (
        <ReactFlowProvider>
            <ReactFlow
                elements={graph as any}
                style={{ width: '100%', height: '100%' }}
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
    );
};

export default Graph;
