import { useEffect, useState } from 'react';
import ReactFlow, { Controls, Background } from 'react-flow-renderer';
import { TGraphElement } from './types/TGraphElement';
import { useGraphContext } from '../../contexts';
import { layoutGraph } from './util/layoutGraph';

const Graph: React.FC = (): JSX.Element => {
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
                position: { x: 0, y: 0 },
                targetPosition: 'left',
                sourcePosition: 'right',
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

        setGraph(layoutGraph(deserializedGraph));
    }, [serializedGraph]);

    return (
        <ReactFlow
            elements={graph as any}
            snapToGrid={true}
            style={{ width: '100%', height: '100%' }}
        >
            <Controls />
            <Background color="#2a2a2a" />
        </ReactFlow>
    );
};

export default Graph;
