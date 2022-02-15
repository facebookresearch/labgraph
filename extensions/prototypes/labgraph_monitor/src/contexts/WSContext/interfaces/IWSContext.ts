import { Dispatch, SetStateAction } from 'react';
import IGraph from './IGraph';

interface IWSContext {
    graph: IGraph;
    mock: string;
    setMock: Dispatch<SetStateAction<string>>;
    endPoint: string;
    setEndPoint: Dispatch<SetStateAction<string>>;
    isConnected: boolean;
    setIsConnected: Dispatch<SetStateAction<boolean>>;
}

export default IWSContext;
