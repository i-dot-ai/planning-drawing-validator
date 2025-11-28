/**
 * Chakra UI v3 Type Augmentations
 *
 * Chakra UI 3.x has incomplete TypeScript type definitions for compound components.
 * Many compound component parts don't properly declare `children` in their props.
 *
 * This declaration file augments the types to include children and other missing props.
 * Add new interfaces here as needed when encountering type errors with compound components.
 */

import { ReactNode } from "react";

// Common style props that should be available on compound components
interface ChakraStyleProps {
  // Spacing
  p?: number | string | Record<string, number | string>;
  px?: number | string | Record<string, number | string>;
  py?: number | string | Record<string, number | string>;
  pt?: number | string | Record<string, number | string>;
  pb?: number | string | Record<string, number | string>;
  pl?: number | string | Record<string, number | string>;
  pr?: number | string | Record<string, number | string>;
  m?: number | string | Record<string, number | string>;
  mx?: number | string | Record<string, number | string>;
  my?: number | string | Record<string, number | string>;
  mt?: number | string | Record<string, number | string>;
  mb?: number | string | Record<string, number | string>;
  ml?: number | string | Record<string, number | string>;
  mr?: number | string | Record<string, number | string>;
  gap?: number | string | Record<string, number | string>;

  // Sizing
  w?: string | number;
  h?: string | number;
  width?: string | number;
  height?: string | number;
  minW?: string;
  maxW?: string;
  minH?: string;
  maxH?: string;

  // Colors
  bg?: string;
  color?: string;
  borderColor?: string;

  // Typography
  fontSize?: string | Record<string, string>;
  fontWeight?: string;
  lineHeight?: string | number;
  letterSpacing?: string;
  textAlign?: string;

  // Borders
  borderRadius?: string;
  borderWidth?: string;
  border?: string;
  borderBottomWidth?: string;
  borderBottomColor?: string;

  // Layout
  display?: string;
  flexDirection?: string;
  alignItems?: string;
  justifyContent?: string;
  flexWrap?: string;
  flex?: string | number;
  flexShrink?: number;
  flexGrow?: number;

  // Effects
  shadow?: string;
  boxShadow?: string;
  opacity?: number;
  cursor?: string;
  overflow?: string;
  overflowX?: string;
  overflowY?: string;

  // Position
  position?: string;
  top?: string | number;
  right?: string | number;
  bottom?: string | number;
  left?: string | number;
  zIndex?: number;
}

declare module "@chakra-ui/react" {
  // ============================================
  // Accordion compound components
  // ============================================
  interface AccordionRootProps extends ChakraStyleProps {
    children?: ReactNode;
    collapsible?: boolean;
  }

  interface AccordionItemProps extends ChakraStyleProps {
    children?: ReactNode;
    value?: string;
  }

  interface AccordionItemTriggerProps extends ChakraStyleProps {
    children?: ReactNode;
    _hover?: Record<string, string>;
  }

  interface AccordionItemContentProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface AccordionItemIndicatorProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // Drawer compound components
  // ============================================
  interface DrawerRootProps extends ChakraStyleProps {
    children?: ReactNode;
    open?: boolean;
    onOpenChange?: (e: { open: boolean }) => void;
    placement?: "start" | "end" | "top" | "bottom";
  }

  interface DrawerBackdropProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface DrawerPositionerProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface DrawerContentProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface DrawerHeaderProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface DrawerTitleProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface DrawerCloseTriggerProps extends ChakraStyleProps {
    children?: ReactNode;
    asChild?: boolean;
  }

  interface DrawerBodyProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface DrawerFooterProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // Tabs compound components
  // ============================================
  interface TabsRootProps extends ChakraStyleProps {
    children?: ReactNode;
    variant?: string;
    defaultValue?: string;
  }

  interface TabsListProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface TabsTriggerProps extends ChakraStyleProps {
    children?: ReactNode;
    value?: string;
    _selected?: Record<string, string>;
  }

  interface TabsContentProps extends ChakraStyleProps {
    children?: ReactNode;
    value?: string;
  }
}
