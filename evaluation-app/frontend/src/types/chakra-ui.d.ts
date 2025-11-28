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
  p?: number | string;
  px?: number | string;
  py?: number | string;
  pt?: number | string;
  pb?: number | string;
  pl?: number | string;
  pr?: number | string;
  m?: number | string;
  mx?: number | string;
  my?: number | string;
  mt?: number | string;
  mb?: number | string;
  ml?: number | string;
  mr?: number | string;
  gap?: number | string;

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
  fontSize?: string;
  fontWeight?: string;
  lineHeight?: string | number;
  letterSpacing?: string;
  textAlign?: string;

  // Borders
  borderRadius?: string;
  borderWidth?: string;
  border?: string;

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
  // Tooltip compound components
  // ============================================
  interface TooltipTriggerProps {
    children?: ReactNode;
    asChild?: boolean;
  }

  interface TooltipPositionerProps {
    children?: ReactNode;
  }

  interface TooltipContentProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // Menu compound components
  // ============================================
  interface MenuTriggerProps {
    children?: ReactNode;
    asChild?: boolean;
  }

  interface MenuPositionerProps {
    children?: ReactNode;
  }

  interface MenuContentProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface MenuItemProps extends ChakraStyleProps {
    children?: ReactNode;
    value?: string;
    onClick?: () => void;
  }

  // ============================================
  // Dialog compound components
  // ============================================
  interface DialogPositionerProps {
    children?: ReactNode;
  }

  interface DialogContentProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface DialogCloseTriggerProps {
    children?: ReactNode;
    asChild?: boolean;
  }

  // ============================================
  // Collapsible compound components
  // ============================================
  interface CollapsibleContentProps {
    children?: ReactNode;
    asChild?: boolean;
  }

  // ============================================
  // RadioGroup compound components
  // ============================================
  interface RadioGroupItemProps extends ChakraStyleProps {
    children?: ReactNode;
    value?: string;
  }

  interface RadioGroupItemTextProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface RadioGroupItemIndicatorProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // Switch compound components
  // ============================================
  interface SwitchRootProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface SwitchControlProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface SwitchThumbProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface SwitchHiddenInputProps {
    children?: ReactNode;
  }

  // ============================================
  // Checkbox compound components
  // ============================================
  interface CheckboxRootProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface CheckboxControlProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface CheckboxHiddenInputProps {
    children?: ReactNode;
  }

  interface CheckboxIndicatorProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // Progress compound components
  // ============================================
  interface ProgressRootProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface ProgressTrackProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface ProgressRangeProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // Field compound components
  // ============================================
  interface FieldRootProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface FieldLabelProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface FieldHelperTextProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface FieldErrorTextProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // NativeSelect compound components
  // ============================================
  interface NativeSelectRootProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface NativeSelectFieldProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // Card compound components
  // ============================================
  interface CardRootProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface CardHeaderProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface CardBodyProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface CardFooterProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  // ============================================
  // Tabs compound components
  // ============================================
  interface TabsRootProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface TabsListProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface TabsTriggerProps extends ChakraStyleProps {
    children?: ReactNode;
    value?: string;
  }

  interface TabsContentProps extends ChakraStyleProps {
    children?: ReactNode;
    value?: string;
  }

  // ============================================
  // Popover compound components
  // ============================================
  interface PopoverTriggerProps {
    children?: ReactNode;
    asChild?: boolean;
  }

  interface PopoverPositionerProps {
    children?: ReactNode;
  }

  interface PopoverContentProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface PopoverHeaderProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface PopoverBodyProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface PopoverCloseTriggerProps {
    children?: ReactNode;
    asChild?: boolean;
  }

  // ============================================
  // Accordion compound components
  // ============================================
  interface AccordionRootProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface AccordionItemProps extends ChakraStyleProps {
    children?: ReactNode;
    value?: string;
  }

  interface AccordionItemTriggerProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface AccordionItemContentProps extends ChakraStyleProps {
    children?: ReactNode;
  }

  interface AccordionItemIndicatorProps extends ChakraStyleProps {
    children?: ReactNode;
  }
}
