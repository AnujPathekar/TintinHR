import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: { extend: { colors: { ink: "#17233c", lime: "#b8ed3b", mist: "#f3f6f8" } } },
  plugins: [],
} satisfies Config;

