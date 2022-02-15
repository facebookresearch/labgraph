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
import startStreamRequest from './json/startStreamRequest.json';
import endStreamRequest from './json/endStreamRequest.json';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import _ from 'lodash';

const GraphContext = createContext<IWSContext>({} as IWSContext);
export const useWSContext = (): IWSContext => useContext(GraphContext);

const WSContextProvider: React.FC<ReactNode> = ({ children }): JSX.Element => {
    const [graph, setGraph] = useState<IGraph>({} as IGraph);
    const [endPoint, setEndPoint] = useState<string>('');
    const [isConnected, setIsConnected] = useState<boolean>(false);
    const [mock, setMock] = useState<string>(MOCK.DEMO);
    const demo_graph = useMemo(() => selectMock(mock), [mock]);

    useEffect(() => {
        if (endPoint) return;
        const {
            stream_batch: {
                'labgraph.monitor': { samples },
            },
        } = demo_graph;
        setGraph(samples[0]['data']);
    }, [demo_graph, setGraph, endPoint]);

    useEffect(() => {
        if (!endPoint) return;
        const client = new W3CWebSocket(endPoint);
        client.onopen = () => {
            client.send(JSON.stringify(startStreamRequest));
            setIsConnected(true);
        };
        client.onmessage = (message) => {
            const parsedData = JSON.parse(message.data as any);

            const {
                stream_batch: {
                    'labgraph.monitor': { samples },
                },
            } = parsedData;

            if (!_.isEqual(samples[0]['data'], graph)) {
                setGraph(samples[0]['data']);
            }
        };
        return () => {
            client.send(endStreamRequest);
            client.close();
        };
    }, [endPoint, graph]);

    return (
        <GraphContext.Provider
            value={{
                graph,
                mock,
                setMock,
                endPoint,
                setEndPoint,
                isConnected,
                setIsConnected,
            }}
        >
            {children}
        </GraphContext.Provider>
    );
};

export default WSContextProvider;
