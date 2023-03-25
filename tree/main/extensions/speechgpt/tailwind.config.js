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
        'custom-gray': '#45484E',
        'custom-blue': '#1877F2',
      },
      gridTemplateColumns: {
        sidebar: "300px auto", //for sidebar layout
        "sidebar-collapsed": "64px auto", //for collapsed sidebar layout
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
				}
			});
		})
	],
}
