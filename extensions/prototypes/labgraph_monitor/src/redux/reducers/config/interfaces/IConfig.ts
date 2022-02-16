import { Edge, Node } from 'react-flow-renderer';

interface IConfig {
    panelOpen: boolean;
    tabIndex: string;
    selectedNode: Node;
    selectedEdge: Edge;
}

export default IConfig;
