import dagre from 'dagre';
import { isNode, isEdge } from 'react-flow-renderer';
import { TGraphElement } from '../types/TGraphElement';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

export const layoutGraph = (
    elements: Array<TGraphElement>,
    layout: string
): Array<TGraphElement> => {
    dagreGraph.setGraph({ rankdir: layout === 'horizontal' ? 'LR' : 'TB' });
    elements.forEach((el: any) => {
        if (isNode(el)) {
            dagreGraph.setNode(el.id, { width: 250, height: 150 });
        } else if (isEdge(el)) {
            dagreGraph.setEdge(el.source, el.target);
        }
    });

    dagre.layout(dagreGraph);

    return elements.map((el: any) => {
        if (isNode(el)) {
            const { x, y } = dagreGraph.node(el.id);
            el.position = {
                x: x,
                y: y,
            };
        }

        return el;
    });
};
