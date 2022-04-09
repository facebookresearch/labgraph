/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { Edge, Node } from 'react-flow-renderer';

interface IConfig {
    panelOpen: boolean;
    tabIndex: string;
    selectedNode: Node;
    selectedEdge: Edge;
}

export default IConfig;
