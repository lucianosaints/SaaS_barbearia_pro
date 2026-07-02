/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#121212', // Fundo principal super escuro
          paper: '#1e1e1e',      // Fundo secundário (cards/modais)
          darker: '#0a0a0a',     // Fundo extra escuro
        },
        gold: {
          light: '#f5df9e',
          DEFAULT: '#d4af37',  // Dourado clássico para detalhes e acentos
          dark: '#aa841c',
        },
        accent: {
          orange: '#f97316',   // Laranja para destaque de interações críticas/botões
          gold: '#d4af37',
        },
        text: {
          primary: '#ffffff',
          secondary: '#a0a0a0',
          muted: '#666666',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
