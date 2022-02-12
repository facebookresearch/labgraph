interface IUIContext {
    mode: 'light' | 'dark';
    toggleMode: () => void;
    layout: 'horizontal' | 'vertical';
    toggleLayout: () => void;
}

export default IUIContext;
