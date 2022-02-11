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
                style: {
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    width: '120px',
                    height: '120px',
                    borderRadius: '50%',
                    fontWeight: '500',
                },
            });

            data.upstreams.forEach((upstream) => {
                deserializedGraph.push({
                    id: `e${upstream}-${name}`,
                    label: `MName(MType)`,
                    source: upstream,
                    target: name,
                    arrowHeadType: 'arrow',
                    type: 'default',
                    animated: nodes[upstream].upstreams.length ? false : true,
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
                }}
            />
            <Background size={0} />
        </ReactFlow>
    );
};

export default Graph;
