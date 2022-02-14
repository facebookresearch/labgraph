import { ReactNode, useState, createContext, useContext, useMemo } from 'react';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import IUIContext from './interfaces/IUIContext';

const UIContext = createContext<IUIContext>({} as IUIContext);
export const useUIContext = (): IUIContext => useContext(UIContext);

const UIContextProvider: React.FC<ReactNode> = ({ children }): JSX.Element => {
    const [mode, setMode] = useState<'light' | 'dark'>('dark');
    const [layout, setLayout] = useState<'horizontal' | 'vertical'>(
        'horizontal'
    );
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