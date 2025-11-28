import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

/**
 * Chakra UI 3 Theme Configuration
 *
 * Design System: Minimal & Clean
 * See src/lib/design-tokens.ts for the design token reference.
 */
const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        brand: {
          50: { value: "#FAFAF9" },
          100: { value: "#F5F5F4" },
          200: { value: "#E7E5E4" },
          300: { value: "#D6D3D1" },
          400: { value: "#A8A29E" },
          500: { value: "#78716C" },
          600: { value: "#57534E" },
          700: { value: "#44403C" },
          800: { value: "#292524" },
          900: { value: "#1C1917" },
        },
        success: {
          50: { value: "#F0FDF4" },
          100: { value: "#DCFCE7" },
          200: { value: "#BBF7D0" },
          300: { value: "#86EFAC" },
          400: { value: "#4ADE80" },
          500: { value: "#22C55E" },
          600: { value: "#16A34A" },
          700: { value: "#15803D" },
          800: { value: "#166534" },
          900: { value: "#14532D" },
        },
        error: {
          50: { value: "#FEF2F2" },
          100: { value: "#FEE2E2" },
          200: { value: "#FECACA" },
          300: { value: "#FCA5A5" },
          400: { value: "#F87171" },
          500: { value: "#EF4444" },
          600: { value: "#DC2626" },
          700: { value: "#B91C1C" },
          800: { value: "#991B1B" },
          900: { value: "#7F1D1D" },
        },
        warning: {
          50: { value: "#FFFBEB" },
          100: { value: "#FEF3C7" },
          200: { value: "#FDE68A" },
          300: { value: "#FCD34D" },
          400: { value: "#FBBF24" },
          500: { value: "#F59E0B" },
          600: { value: "#D97706" },
          700: { value: "#B45309" },
          800: { value: "#92400E" },
          900: { value: "#78350F" },
        },
      },
      fonts: {
        heading: {
          value: `"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`,
        },
        body: {
          value: `"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`,
        },
      },
    },
    semanticTokens: {
      colors: {
        "bg.canvas": { value: "#FAFAF9" },
        "bg.surface": { value: "#FFFFFF" },
        "bg.subtle": { value: "#F5F5F4" },
        "bg.muted": { value: "#F5F5F4" },
        "bg.emphasis": { value: "#1C1917" },
        "fg.emphasis": { value: "#1C1917" },
        "fg.default": { value: "#44403C" },
        "fg.muted": { value: "#78716C" },
        "fg.subtle": { value: "#A8A29E" },
        "fg.onEmphasis": { value: "#FAFAF9" },
        "border.default": { value: "#E7E5E4" },
        "border.muted": { value: "#F5F5F4" },
        "border.emphasis": { value: "#D6D3D1" },
        "interactive.hover": { value: "#F5F5F4" },
        "interactive.active": { value: "#E7E5E4" },
      },
    },
  },
  globalCss: {
    body: {
      bg: "bg.canvas",
      color: "fg.default",
      letterSpacing: "-0.01em",
      lineHeight: 1.625,
    },
    "h1, h2, h3, h4, h5, h6": {
      color: "fg.emphasis",
      letterSpacing: "-0.02em",
      lineHeight: 1.15,
      fontWeight: 600,
    },
  },
});

export const system = createSystem(defaultConfig, config);

export default system;
