interface INode {
    id: string;
    data: {
        label: string;
    };
    position: {
        x: number;
        y: number;
    };

    sourcePosition: 'right' | 'bottom';
    targetPosition: 'left' | 'top';
}

export default INode;
