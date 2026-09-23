/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: { DEFAULT: '#07111f', paper: '#0d1b2e', darker: '#030914' },
        gold: { light: '#ff9f8f', DEFAULT: '#ff5c6c', dark: '#e73f59' },
        accent: { orange: '#ff7a45', gold: '#21d4d8' },
        text: { primary: '#f7fbff', secondary: '#b6c6d9', muted: '#71839a' },
      },
      fontFamily: { sans: ['Manrope', 'Inter', 'sans-serif'] },
      boxShadow: { glow: '0 24px 80px rgba(255, 92, 108, 0.2)' },
    },
  },
  plugins: [],
}
