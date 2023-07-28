/** @type {import('tailwindcss').Config} */
const plugin = require('tailwindcss/plugin');
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'custom-black': '#1c2b33',
        'custom-gray': { 100: '#F2F4F7', 200: '#67788a' },
        'custom-blue': '#2962D8',
      },
      gridTemplateColumns: {
        sidebar: '300px auto', //for sidebar layout
        'sidebar-collapsed': '64px auto', //for collapsed sidebar layout
      },
    },
  },
  plugins: [
    plugin(function ({ addUtilities }) {
      addUtilities({
        '.drag-none': {
          '-webkit-user-drag': 'none',
          '-khtml-user-drag': 'none',
          '-moz-user-drag': 'none',
          '-o-user-drag': 'none',
          'user-drag': 'none',
          'user-select': 'none',
        },
      });
    }),
  ],
};
