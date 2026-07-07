/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Role accent colors per spec §10 Design System Tokens
        primary: "#1B5E20", // Resident
        accent: "#0277BD", // Collector
        manager: "#B8860B", // Manager
        recycler: "#6A1B9A", // Recycler
        admin: "#37474F", // Admin
        success: "#2E7D32",
        warn: "#ED6C02",
        danger: "#C62828",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        card: "12px",
        input: "8px",
      },
      boxShadow: {
        soft: "0 1px 3px rgba(0,0,0,0.08)",
        elevated: "0 4px 12px rgba(0,0,0,0.10)",
      },
    },
  },
  plugins: [],
};
