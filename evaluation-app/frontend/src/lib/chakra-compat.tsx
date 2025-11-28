/**
 * Chakra UI v3 Compatibility Helpers
 *
 * This file provides convenience wrapper components for common Chakra UI patterns.
 * Type definitions for compound components are handled in /src/types/chakra-ui.d.ts
 */

import React, { ReactNode } from "react";
import { Tooltip as ChakraTooltip, Portal } from "@chakra-ui/react";

// ─────────────────────────────────────────────────
// SIMPLE TOOLTIP
// A convenience wrapper for the common tooltip pattern
// ─────────────────────────────────────────────────

interface SimpleTooltipProps {
  label: string;
  children: ReactNode;
  placement?: "top" | "bottom" | "left" | "right";
  maxW?: string;
}

export function SimpleTooltip({
  label,
  children,
  placement = "top",
  maxW = "280px",
}: SimpleTooltipProps) {
  return (
    <ChakraTooltip.Root>
      <ChakraTooltip.Trigger asChild>{children}</ChakraTooltip.Trigger>
      <Portal>
        <ChakraTooltip.Positioner>
          <ChakraTooltip.Content
            bg="gray.800"
            color="white"
            px={3}
            py={2}
            borderRadius="md"
            fontSize="xs"
            maxW={maxW}
          >
            {label}
          </ChakraTooltip.Content>
        </ChakraTooltip.Positioner>
      </Portal>
    </ChakraTooltip.Root>
  );
}
