import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14171F",
        paper: "#F7F5F1",
        paperDim: "#EFEBE3",
        brass: "#B8873B",
        brassDim: "#E4D2AC",
        sage: "#4B7A64",
        clay: "#B4553F",
        slate: "#5B6472",
      },
      fontFamily: {
        display: ["var(--font-fraunces)", "Georgia", "serif"],
        body: ["var(--font-plex)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
