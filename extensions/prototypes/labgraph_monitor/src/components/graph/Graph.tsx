import { useEffect, useState } from 'react';
import ReactFlow, { Controls, Background } from 'react-flow-renderer';
import { TGraphElement } from './types/GraphElement';
import { useGraphContext } from '../../contexts';

const Graph: React.FC = () => {
    const { graph: serializedGraph } = useGraphContext();
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
                position: {
                    x: Math.floor(Math.random() * 1000),
                    y: Math.floor(Math.random() * 1000),
                },
            });

            data.upstreams.forEach((upstream) => {
                deserializedGraph.push({
                    id: `e${upstream}-${name}`,
                    source: upstream,
                    target: name,
                    label: `MName(MType)`,
                });
            });
        }

        setGraph(deserializedGraph);
    }, [serializedGraph]);

    return (
        <ReactFlow
            elements={graph}
            snapToGrid={true}
            snapGrid={[15, 15]}
            style={{ width: '100%', height: '100%' }}
        >
            <Controls />
            <Background color="#aaa" gap={16} />
        </ReactFlow>
    );
};

export default Graph;
