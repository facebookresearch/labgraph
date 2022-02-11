interface INode {
    id: string;
    data: {
        label: string;
    };
    position: {
        x: number;
        y: number;
    };
}

export default INode;
