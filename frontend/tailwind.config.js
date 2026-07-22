/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // High quality design color system tokens
        brand: {
          light: '#3b82f6',
          dark: '#60a5fa',
        }
      }
    },
  },
  plugins: [],
}
