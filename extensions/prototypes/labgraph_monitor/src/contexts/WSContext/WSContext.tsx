/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import { ReactNode, useRef, createContext, useEffect } from 'react';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import { RootState } from '../../redux/store';
import { useSelector, useDispatch } from 'react-redux';
import {
    setConnection,
    setGraph,
} from '../../redux/reducers/graph/ws/WSReducer';
import { copyRealtimeGraph } from '../../redux/reducers/graph/mock/mockReducer';
import WS_STATE from '../../redux/reducers/graph/ws/enums/WS_STATE';
import startStreamRequest from './json/startStreamRequest.json';
import endStreamRequest from './json/endStreamRequest.json';
import _ from 'lodash';

const GraphContext = createContext<{}>({});

/**
 * A context component used to share WebSocket related information with different component.
 * All interactions with the LabGraph WebSockets API are happening inside this context.
 *
 * @param {ReactNode} props represents the react components wrapped by this context
 * @returns {JSX.Element}
 */
const WSContextProvider: React.FC<ReactNode> = ({ children }): JSX.Element => {
    const { connection, graph } = useSelector((state: RootState) => state.ws);

    const clientRef = useRef<W3CWebSocket | null>(null);
    const dispatch = useDispatch();

    useEffect(() => {
        if (!process.env.REACT_APP_WS_API) {
            alert('Error: Undefined Environment Variable: REACT_APP_WS_API');
            dispatch(setConnection(WS_STATE.DISCONNECTED));
            // dispatch to be disocnnected disconnect
            return;
        }
        switch (connection) {
            case WS_STATE.IS_CONNECTING:
                try {
                    clientRef.current = new W3CWebSocket(
                        process.env.REACT_APP_WS_API as string
                    );

                    clientRef.current.onopen = () => {
                        clientRef.current?.send(
                            JSON.stringify(startStreamRequest)
                        );
                        dispatch(setConnection(WS_STATE.CONNECTED));
                    };

                    clientRef.current.onerror = (err: any) => {
                        dispatch(setConnection(WS_STATE.DISCONNECTED));
                    };
                } catch (error) {
                    // catch error
                }
                break;
            case WS_STATE.CONNECTED:
                if (!clientRef.current) return;
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
                clientRef.current?.send(JSON.stringify(endStreamRequest));
                clientRef.current?.close();
                dispatch(setConnection(WS_STATE.DISCONNECTED));
                dispatch(copyRealtimeGraph(graph));
        }
    }, [connection, graph, dispatch]);

    return <GraphContext.Provider value={{}}>{children}</GraphContext.Provider>;
};

export default WSContextProvider;
