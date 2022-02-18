/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import dagre from 'dagre';
import { isNode, isEdge } from 'react-flow-renderer';
import { TGraphElement } from '../types/TGraphElement';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

/**
 * A function used to update the graph layout
 *
 * @param {Array<TGraphElement} elements: Nodes and Edges of the computational graph
 * @param {string} layout: The direction of the nodes and edges.
 *                         It can be either 'horizontal' or 'vertical'
 * @returns {Array<TGraphElement} The new array of nodes and edges
 */
export const layoutGraph = (
    elements: Array<TGraphElement>,
    layout: string
): Array<TGraphElement> => {
    dagreGraph.setGraph({ rankdir: layout === 'horizontal' ? 'LR' : 'TB' });
    elements.forEach((el: any) => {
        if (isNode(el)) {
            dagreGraph.setNode(el.id, { width: 400, height: 200 });
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
