import React, { ReactNode, useState, createContext, useContext } from 'react';
import { Edge, Node } from 'react-flow-renderer';
import IConfigContext from './interfaces/IGraphSettingContext';

const ConfigContext = createContext<IConfigContext>({} as IConfigContext);
export const useConfigContext = (): IConfigContext => useContext(ConfigContext);

const ConfigContextProvider: React.FC<ReactNode> = ({
    children,
}): JSX.Element => {
    const [panel, setPanel] = useState({
        isOpen: false,
        panelIndex: '1',
    });
    const [selectedNode, setSelectedNode] = useState<Node>({} as Node);
    const [selectedEdge, setSelectedEdge] = useState<Edge>({} as Edge);
    return (
        <ConfigContext.Provider
            value={{
                panel,
                setPanel,
                selectedNode,
                setSelectedNode,
                selectedEdge,
                setSelectedEdge,
            }}
        >
            {children}
        </ConfigContext.Provider>
    );
};
export default ConfigContextProvider;
