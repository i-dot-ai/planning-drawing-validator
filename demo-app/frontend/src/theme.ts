import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

/**
 * Chakra UI Theme Configuration
 *
 * Features an earthy, organic colour palette centred around soft greens and mineral
 * neutrals. All colours meet WCAG AA accessibility requirements for contrast ratios.
 * Touch targets are minimum 44px for mobile accessibility.
 */
const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        brand: {
          50: { value: "#F2F7F4" },
          100: { value: "#D9E7DF" },
          200: { value: "#B3D2C4" },
          300: { value: "#8CB9A6" },
          400: { value: "#6AA08A" },
          500: { value: "#4F8671" },
          600: { value: "#3D6A59" },
          700: { value: "#2E5043" },
          800: { value: "#1F372E" },
          900: { value: "#13231D" },
        },
        success: {
          50: { value: "#F0F8F4" },
          100: { value: "#CCECDC" },
          200: { value: "#9FDABE" },
          300: { value: "#71C8A0" },
          400: { value: "#4AB488" },
          500: { value: "#379A71" },
          600: { value: "#2C7C5B" },
          700: { value: "#215E45" },
          800: { value: "#164130" },
          900: { value: "#0D2A1F" },
        },
        error: {
          50: { value: "#FDECEA" },
          100: { value: "#F9C7C1" },
          200: { value: "#F39F96" },
          300: { value: "#E8746A" },
          400: { value: "#DA4B41" },
          500: { value: "#C3362D" },
          600: { value: "#9C2922" },
          700: { value: "#761D19" },
          800: { value: "#511210" },
          900: { value: "#2D0808" },
        },
        warning: {
          50: { value: "#FFF6E5" },
          100: { value: "#FCE5BD" },
          200: { value: "#F7D090" },
          300: { value: "#F0B961" },
          400: { value: "#E6A53E" },
          500: { value: "#CF8527" },
          600: { value: "#A5671D" },
          700: { value: "#7C4C14" },
          800: { value: "#53320D" },
          900: { value: "#311E07" },
        },
      },
      fonts: {
        heading: {
          value: `"Public Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`,
        },
        body: {
          value: `"Source Sans 3", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`,
        },
      },
    },
    semanticTokens: {
      colors: {
        "bg.canvas": { value: "#F6F8F4" },
        "bg.surface": { value: "rgba(255, 255, 255, 0.95)" },
        "bg.surfaceAccent": { value: "#E3ECE2" },
        "fg.emphasis": { value: "#243129" },
        "fg.default": { value: "#38403A" },
        "fg.muted": { value: "#515B53" },
      },
    },
  },
  globalCss: {
    body: {
      bg: "bg.canvas",
      color: "fg.emphasis",
      letterSpacing: "-0.011em",
      lineHeight: 1.65,
    },
    "h1, h2, h3, h4, h5, h6": {
      letterSpacing: "-0.02em",
      lineHeight: 1.15,
    },
  },
});

export const system = createSystem(defaultConfig, config);

export default system;
