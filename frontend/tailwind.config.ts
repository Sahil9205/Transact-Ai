import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          base: "#FFF9F2",
          soft: "#FFF4E6",
        },
        peach: {
          light: "#FFE8C7",
          warm: "#FFD9A8",
          soft: "#FFC978",
        },
        brand: {
          orange: "#FF9F1C",
          "orange-deep": "#FF7A18",
          red: "#FF203D",
          "red-deep": "#E71937",
        },
        charcoal: {
          primary: "#171717",
          secondary: "#5F5F5F",
          muted: "#8A8A8A",
        },
        border: {
          soft: "#F0DED0",
          strong: "#E8CDBB",
        }
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
      boxShadow: {
        card: "0 2px 12px rgba(240, 222, 208, 0.45)",
        elevated: "0 12px 32px rgba(240, 222, 208, 0.6)",
      }
    },
  },
  plugins: [],
};
export default config;
