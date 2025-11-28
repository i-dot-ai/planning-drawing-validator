/**
 * Design Tokens
 *
 * Central source of truth for all design values.
 * Use these tokens throughout the application for consistency.
 */

// ─────────────────────────────────────────────────
// SPACING (consistent rhythm based on 4px grid)
// ─────────────────────────────────────────────────
export const spacing = {
  xs: 1, // 4px - tight inline spacing
  sm: 2, // 8px - between related elements
  md: 3, // 12px - between groups
  lg: 4, // 16px - section padding
  xl: 6, // 24px - major sections
  "2xl": 8, // 32px - page-level spacing
} as const;

// ─────────────────────────────────────────────────
// RADII (visual hierarchy: larger = more prominent)
// ─────────────────────────────────────────────────
export const radii = {
  none: 0,
  sm: "sm", // 4px - buttons, inputs
  md: "md", // 6px - badges, chips
  lg: "lg", // 8px - cards, containers
  xl: "xl", // 12px - modals, panels
  full: "full", // pills, avatars
} as const;

// ─────────────────────────────────────────────────
// TYPOGRAPHY
// ─────────────────────────────────────────────────
export const fontSize = {
  xs: "xs", // 11px - labels, metadata
  sm: "sm", // 13px - secondary text
  md: "md", // 14px - body (default)
  lg: "lg", // 16px - emphasized
  xl: "xl", // 18px - subheadings
  "2xl": "2xl", // 24px - headings
} as const;

export const fontWeight = {
  normal: "normal", // 400
  medium: "medium", // 500
  semibold: "semibold", // 600
} as const;

// ─────────────────────────────────────────────────
// ICONS (3-tier system)
// ─────────────────────────────────────────────────
export const iconSize = {
  sm: 3.5, // 14px - inline, badges
  md: 4, // 16px - buttons, default
  lg: 5, // 20px - emphasis, headers
} as const;

// ─────────────────────────────────────────────────
// TRANSITIONS
// ─────────────────────────────────────────────────
export const transition = {
  fast: "all 0.1s ease", // hover states
  normal: "all 0.15s ease", // buttons, toggles
  slow: "all 0.25s ease", // panels, modals
  expand: "all 0.2s ease-out", // collapse/expand
} as const;

// ─────────────────────────────────────────────────
// Z-INDEX SCALE (layering system)
// ─────────────────────────────────────────────────
export const zIndex = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  overlay: 30,
  modal: 40,
  tooltip: 50,
} as const;

// ─────────────────────────────────────────────────
// LAYOUT (container widths)
// ─────────────────────────────────────────────────
export const layout = {
  maxWidth: {
    content: "7xl", // Main content area
    modal: "2xl", // Modal dialogs
    card: "280px", // Stat cards, metric boxes
    text: "md", // Text blocks for readability
  },
  containerPadding: {
    x: 6, // Horizontal page padding
    y: 8, // Vertical page padding
  },
} as const;

// ─────────────────────────────────────────────────
// ANIMATIONS (keyframes and presets)
// ─────────────────────────────────────────────────
export const animation = {
  pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
  fadeIn: { initial: { opacity: 0 }, animate: { opacity: 1 } },
  slideUp: { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } },
  slideDown: { initial: { opacity: 0, y: -10 }, animate: { opacity: 1, y: 0 } },
} as const;

// ─────────────────────────────────────────────────
// COLORS (semantic)
// ─────────────────────────────────────────────────
export const colors = {
  // Primary actions
  primary: {
    bg: "gray.900",
    bgHover: "gray.800",
    bgActive: "gray.700",
    text: "white",
  },
  // Secondary/ghost actions
  secondary: {
    bg: "transparent",
    bgHover: "gray.100",
    text: "gray.600",
    textHover: "gray.900",
  },
  // Muted/tertiary
  muted: {
    bg: "gray.50",
    bgHover: "gray.100",
    text: "gray.500",
    textHover: "gray.700",
  },
  // Borders
  border: {
    default: "gray.200",
    hover: "gray.300",
    focus: "blue.500",
  },
  // Text hierarchy
  text: {
    primary: "gray.900",
    secondary: "gray.600",
    muted: "gray.500",
    disabled: "gray.400",
  },
  // Status (full palette for each)
  status: {
    success: {
      text: "green.700",
      bg: "green.50",
      border: "green.200",
      icon: "green.600",
    },
    error: {
      text: "red.700",
      bg: "red.50",
      border: "red.200",
      icon: "red.600",
    },
    warning: {
      text: "orange.700",
      bg: "orange.50",
      border: "orange.200",
      icon: "orange.600",
    },
    info: {
      text: "blue.700",
      bg: "blue.50",
      border: "blue.200",
      icon: "blue.600",
    },
    neutral: {
      text: "gray.700",
      bg: "gray.100",
      border: "gray.200",
      icon: "gray.500",
    },
  },
  // Accent bars (left border indicators on cards)
  accent: {
    primary: "gray.900",
    active: "blue.400",
    success: "green.400",
    error: "red.400",
    warning: "orange.400",
    muted: "gray.200",
  },
} as const;

// ─────────────────────────────────────────────────
// COMPONENT TOKENS
// ─────────────────────────────────────────────────
export const components = {
  button: {
    size: {
      sm: { h: 8, px: 3, fontSize: "sm" }, // 32px height
      md: { h: 9, px: 4, fontSize: "sm" }, // 36px height
      lg: { h: 10, px: 5, fontSize: "md" }, // 40px height
    },
    iconGap: 1.5, // 6px
  },
  input: {
    size: {
      sm: { h: 8, px: 3 },
      md: { h: 9, px: 3 },
      lg: { h: 10, px: 4 },
    },
  },
  card: {
    padding: 4, // 16px
    headerPadding: 3, // 12px
    gap: 3, // 12px
    borderRadius: "lg",
  },
  badge: {
    h: 5.5, // 22px
    px: 2, // 8px
    fontSize: "xs",
  },
  chip: {
    h: 7, // 28px
    px: 3, // 12px
    fontSize: "sm",
    gap: 1.5, // 6px
  },
  modal: {
    padding: 5, // 20px
    gap: 4, // 16px
    borderRadius: "xl",
  },
} as const;

// ─────────────────────────────────────────────────
// STYLE PRESETS (common patterns)
// ─────────────────────────────────────────────────
export const presets = {
  // Primary button
  buttonPrimary: {
    bg: colors.primary.bg,
    color: colors.primary.text,
    fontWeight: fontWeight.medium,
    borderRadius: radii.sm,
    _hover: { bg: colors.primary.bgHover },
    _active: { bg: colors.primary.bgActive },
    _disabled: { bg: "gray.200", color: "gray.400", cursor: "not-allowed" },
  },
  // Ghost button
  buttonGhost: {
    bg: colors.secondary.bg,
    color: colors.secondary.text,
    fontWeight: fontWeight.medium,
    borderRadius: radii.sm,
    _hover: { bg: colors.secondary.bgHover, color: colors.secondary.textHover },
  },
  // Icon button
  buttonIcon: {
    color: colors.muted.text,
    borderRadius: radii.sm,
    _hover: { bg: colors.muted.bgHover, color: colors.muted.textHover },
  },
  // Card
  card: {
    bg: "white",
    borderRadius: radii.lg,
    border: "1px solid",
    borderColor: colors.border.default,
    _hover: { borderColor: colors.border.hover },
    transition: transition.fast,
  },
  // Input
  input: {
    borderRadius: radii.sm,
    borderColor: colors.border.default,
    _hover: { borderColor: colors.border.hover },
    _focus: {
      borderColor: "gray.900",
      boxShadow: "0 0 0 1px rgba(0, 0, 0, 0.1)",
    },
  },
  // Section label (uppercase headers)
  sectionLabel: {
    fontSize: "xs",
    fontWeight: "semibold",
    textTransform: "uppercase" as const,
    letterSpacing: "wider",
    color: "gray.500",
  },
  // Status badges
  badgeSuccess: {
    bg: "green.50",
    color: "green.700",
    borderRadius: radii.md,
  },
  badgeError: {
    bg: "red.50",
    color: "red.700",
    borderRadius: radii.md,
  },
  badgeWarning: {
    bg: "orange.50",
    color: "orange.700",
    borderRadius: radii.md,
  },
  badgeNeutral: {
    bg: "gray.100",
    color: "gray.700",
    borderRadius: radii.md,
  },
  // Accent bar (left border indicator)
  accentBar: {
    position: "absolute" as const,
    left: 0,
    top: 0,
    bottom: 0,
    width: "2px",
    opacity: 0.3,
  },
} as const;

// Export everything as a single tokens object for convenience
export const tokens = {
  spacing,
  radii,
  fontSize,
  fontWeight,
  iconSize,
  transition,
  zIndex,
  layout,
  animation,
  colors,
  components,
  presets,
} as const;

export default tokens;
