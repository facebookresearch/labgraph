import { Edge, Node } from 'react-flow-renderer';

interface IConfigContext {
    panel: { isOpen: boolean; panelIndex: string };
    setPanel: React.Dispatch<
        React.SetStateAction<{
            isOpen: boolean;
            panelIndex: string;
        }>
    >;
    selectedNode: Node;
    setSelectedNode: React.Dispatch<React.SetStateAction<Node<any>>>;
    selectedEdge: Edge;
    setSelectedEdge: React.Dispatch<React.SetStateAction<Edge<any>>>;
}

export default IConfigContext;
