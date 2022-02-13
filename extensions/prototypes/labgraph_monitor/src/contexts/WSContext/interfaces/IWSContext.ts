import { Dispatch, SetStateAction } from 'react';
import IGraph from './IGraph';

interface IWSContext {
    graph: IGraph;
    setMock: Dispatch<SetStateAction<string>>;
}

export default IWSContext;
