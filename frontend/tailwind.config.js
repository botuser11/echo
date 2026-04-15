export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        echo: {
          950: '#0A0F1C',
          900: '#131A2E',
          850: '#1E2A45',
          amber: '#F59E0B',
          blue: '#3B82F6',
          text: '#F1F5F9',
          muted: '#94A3B8',
        },
      },
      fontFamily: {
        sans: ['DM Sans', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        serif: ['Instrument Serif', 'ui-serif', 'Georgia', 'serif'],
      },
      boxShadow: {
        glow: '0 20px 60px rgba(245, 158, 11, 0.18)',
      },
    },
  },
  plugins: [],
};
