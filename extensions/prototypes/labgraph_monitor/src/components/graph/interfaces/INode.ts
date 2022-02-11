interface INode {
    id: string;
    data: {
        label: string;
    };
    position: {
        x: number;
        y: number;
    };
    sourcePosition: 'left' | 'top' | 'right' | 'bottom';
    targetPosition: 'left' | 'top' | 'right' | 'bottom';
    style: { [property: string]: string };
}

export default INode;
