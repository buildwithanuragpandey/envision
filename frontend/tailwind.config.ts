import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Linear / Notion / Perplexity inspired minimal palette
        light: {
          bg: "#F7F7F5",
          surface: "#FFFFFF",
          subtle: "#F0F0EE",
          border: "#E5E5E3",
          hover: "#EAEAE8",
          text: "#171717",
          muted: "#737373",
        },
        dark: {
          bg: "#111111",
          surface: "#181818",
          subtle: "#202020",
          border: "#2A2A2A",
          hover: "#252525",
          text: "#F5F5F5",
          muted: "#A3A3A3",
        },
        accent: {
          DEFAULT: "#2563EB",
          hover: "#1D4ED8",
          light: "#EFF6FF",
          dark: "#1E3A8A",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "-apple-system", "sans-serif"],
        serif: ["var(--font-source-serif)", "Georgia", "Cambria", "serif"],
        mono: ["var(--font-mono)", "Menlo", "Monaco", "Courier New", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        DEFAULT: "6px",
        md: "8px",
        lg: "10px",
        xl: "12px",
      },
      boxShadow: {
        subtle: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        flyout: "0 4px 12px 0 rgba(0, 0, 0, 0.08)",
        modal: "0 12px 32px 0 rgba(0, 0, 0, 0.12)",
      },
    },
  },
  plugins: [],
};
export default config;
