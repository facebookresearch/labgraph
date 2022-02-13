import {
    ReactNode,
    createContext,
    useContext,
    useState,
    useEffect,
    useMemo,
} from 'react';
import IGraph from './interfaces/IGraph';
import IWSContext from './interfaces/IWSContext';
import { MOCK, selectMock } from '../../mocks';

const GraphContext = createContext<IWSContext>({} as IWSContext);
export const useWSContext = (): IWSContext => useContext(GraphContext);

const WSContextProvider: React.FC<ReactNode> = ({ children }): JSX.Element => {
    const [graph, setGraph] = useState<IGraph>({} as IGraph);
    const [mock, setMock] = useState<string>(MOCK.DEMO);

    const demo_graph = useMemo(() => selectMock(mock), [mock]);

    useEffect(() => {
        const {
            stream_batch: {
                'labgraph.monitor': { samples },
            },
        } = demo_graph;
        setGraph(samples[0]['data']);
    }, [demo_graph]);

    return (
        <GraphContext.Provider
            value={{
                graph,
                mock,
                setMock,
            }}
        >
            {children}
        </GraphContext.Provider>
    );
};

export default WSContextProvider;
