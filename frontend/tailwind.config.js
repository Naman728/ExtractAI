/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        void: {
          DEFAULT: "#F7F8FA",
          deep: "#EEF1F5",
        },
        ink: {
          950: "#0F172A",
          900: "#0F172A",
          800: "#1E293B",
          700: "#334155",
          600: "#475569",
          500: "#64748B",
        },
        accent: {
          DEFAULT: "#0D9488",
          dim: "#0F766E",
          ice: "#5EEAD4",
          blue: "#0284C7",
          soft: "#CCFBF1",
        },
        signal: {
          DEFAULT: "#EA580C",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        grid: "linear-gradient(to right, rgba(15,23,42,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(15,23,42,0.04) 1px, transparent 1px)",
      },
      boxShadow: {
        glow: "0 0 40px rgba(13, 148, 136, 0.12)",
        card: "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.06)",
      },
    },
  },
  plugins: [],
};
