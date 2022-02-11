import {
    ReactNode,
    createContext,
    useContext,
    useState,
    useEffect,
} from 'react';
import IGraph from './interfaces/IGraph';
import IGraphContext from './interfaces/IGraphContext';
import demo from '../../mocks/demo.json';

const GraphContext = createContext<IGraphContext>({} as IGraphContext);
export const useGraphContext = (): IGraphContext => useContext(GraphContext);

const GraphContextProvider: React.FC<ReactNode> = ({ children }) => {
    const [graph, setGraph] = useState<IGraph>({} as IGraph);

    useEffect(() => {
        const {
            stream_batch: {
                'labgraph.monitor': { samples },
            },
        } = demo;

        setGraph(samples[0]['data']);
    }, []);

    return (
        <GraphContext.Provider
            value={{
                graph,
            }}
        >
            {children}
        </GraphContext.Provider>
    );
};

export default GraphContextProvider;
