import { ReactNode, useRef, createContext, useEffect } from 'react';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import { RootState } from '../../redux/store';
import { useSelector, useDispatch } from 'react-redux';
import { setConnection, setGraph } from '../../redux/reducers/ws/WSReducer';
import { copyRealtimeGraph } from '../../redux/reducers/mock/mockReducer';
import WS_STATE from '../../redux/reducers/ws/enums/WS_STATE';
import startStreamRequest from './json/startStreamRequest.json';
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import endStreamRequest from './json/endStreamRequest.json';
import _ from 'lodash';

const GraphContext = createContext<{}>({});

const WSContextProvider: React.FC<ReactNode> = ({ children }): JSX.Element => {
    const { connection, graph } = useSelector((state: RootState) => state.ws);

    const clientRef = useRef<any>(null);
    const dispatch = useDispatch();

    useEffect(() => {
        switch (connection) {
            case WS_STATE.IS_CONNECTING:
                clientRef.current = new W3CWebSocket(
                    process.env.REACT_APP_WS_API as string
                );
                clientRef.current.onopen = () => {
                    clientRef.current.send(JSON.stringify(startStreamRequest));
                    dispatch(setConnection(WS_STATE.CONNECTED));
                };
                break;

            case WS_STATE.CONNECTED:
                clientRef.current.onmessage = (message: any) => {
                    const data = JSON.parse(message.data);
                    if (!data['stream_batch']) return;
                    const {
                        stream_batch: {
                            'labgraph.monitor': { samples },
                        },
                    } = data;
                    if (!_.isEqual(samples[0]['data'], graph)) {
                        dispatch(setGraph(samples[0]['data']));
                    }
                };

                break;

            case WS_STATE.IS_DISCONNECTING:
                clientRef.current.send(JSON.stringify(endStreamRequest));
                clientRef.current.close();
                dispatch(setConnection(WS_STATE.DISCONNECTED));
                dispatch(copyRealtimeGraph(graph));
        }
    }, [connection, graph, dispatch]);

    return <GraphContext.Provider value={{}}>{children}</GraphContext.Provider>;
};

export default WSContextProvider;
