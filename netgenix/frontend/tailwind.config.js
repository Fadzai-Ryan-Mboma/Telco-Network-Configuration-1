/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Backgrounds
        'bg-primary': '#0B1426',
        'bg-card': '#111B2E',
        'bg-card-hover': '#162032',
        'bg-input': '#0D1829',

        // Accents
        'accent-teal': '#00F5D4',
        'accent-green': '#00F19C',
        'accent-purple': '#8B5CF6',
        'accent-orange': '#F59E0B',
        'accent-red': '#EF4444',

        // Status
        'status-success': '#22C55E',
        'status-warning': '#F59E0B',
        'status-error': '#EF4444',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
