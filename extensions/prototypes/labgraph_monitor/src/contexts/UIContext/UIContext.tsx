/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
import {
    ReactNode,
    useState,
    useEffect,
    createContext,
    useContext,
    useMemo,
} from 'react';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import IUIContext from './interfaces/IUIContext';

const UIContext = createContext<IUIContext>({} as IUIContext);
export const useUIContext = (): IUIContext => useContext(UIContext);

/**
 * A context component used to share UI related information with different component
 *
 * @param {ReactNode} props represents the react components wrapped by this context
 * @returns {JSX.Element}
 */
const UIContextProvider: React.FC<ReactNode> = ({ children }): JSX.Element => {
    const localMode = localStorage.getItem('labgraph_monitor_mode') as
        | 'dark'
        | 'light';

    const [mode, setMode] = useState<'light' | 'dark'>(() => {
        return localMode ? localMode : 'dark';
    });
    const [layout, setLayout] = useState<'horizontal' | 'vertical'>(
        'horizontal'
    );

    useEffect(() => {
        return () => {
            localStorage.setItem(
                'labgraph_monitor_mode',
                mode === 'dark' ? 'light' : 'dark'
            );
        };
    }, [mode]);

    const themeObject = useMemo(
        () => ({
            toggleMode: () => {
                setMode((prevMode) =>
                    prevMode === 'light' ? 'dark' : 'light'
                );
            },
            mode,
        }),
        [mode]
    );

    const layoutObject = useMemo(
        () => ({
            toggleLayout: () => {
                setLayout((prevLayout) =>
                    prevLayout === 'horizontal' ? 'vertical' : 'horizontal'
                );
            },
            layout,
        }),
        [layout]
    );

    const theme = useMemo(
        () =>
            createTheme({
                palette: {
                    mode,
                    ...(mode === 'dark'
                        ? {
                              background: {
                                  default: '#111827',
                                  paper: '#1B2533',
                              },
                              text: {
                                  primary: '#F7F7F7',
                                  secondary: '#FFF',
                              },
                          }
                        : {
                              background: {
                                  default: '#FEFEFE',
                                  paper: '#FFF',
                              },
                              text: {
                                  primary: '#111827',
                              },
                          }),
                },
            }),
        [mode]
    );

    return (
        <UIContext.Provider
            value={{
                ...themeObject,
                ...layoutObject,
            }}
        >
            <ThemeProvider theme={theme}>{children}</ThemeProvider>
        </UIContext.Provider>
    );
};

export default UIContextProvider;
