import React from "react";
import { Box, HStack, VStack, Heading } from "@chakra-ui/react";
import { CheckCircle2, XCircle, AlertCircle, LucideIcon } from "lucide-react";
import { MarkdownRenderer } from "./MarkdownRenderer";

export type StatusType = "success" | "error" | "warning" | "info";

interface StatusCardProps {
  status: StatusType;
  title: string;
  description: string;
  actions?: React.ReactNode;
  details?: React.ReactNode;
}

const statusConfig: Record<
  StatusType,
  {
    icon: LucideIcon;
    iconColor: string;
    borderColor: string;
    bg: string;
  }
> = {
  success: {
    icon: CheckCircle2,
    iconColor: "rgba(44, 124, 91, 1)",
    borderColor: "rgba(59, 127, 115, 0.4)",
    bg: "rgba(59, 127, 115, 0.08)",
  },
  error: {
    icon: XCircle,
    iconColor: "rgba(156, 41, 34, 1)",
    borderColor: "rgba(201, 86, 76, 0.4)",
    bg: "rgba(201, 86, 76, 0.08)",
  },
  warning: {
    icon: AlertCircle,
    iconColor: "rgba(124, 76, 20, 1)",
    borderColor: "rgba(203, 162, 61, 0.4)",
    bg: "rgba(203, 162, 61, 0.08)",
  },
  info: {
    icon: AlertCircle,
    iconColor: "rgba(79, 134, 113, 1)",
    borderColor: "rgba(79, 134, 113, 0.3)",
    bg: "rgba(79, 134, 113, 0.08)",
  },
};

/**
 * StatusCard component displays prominent status information with clear visual hierarchy.
 *
 * Features:
 * - Large, clear status indicator with colour-coded icons
 * - High contrast colours for accessibility
 * - Minimum 44px touch targets for mobile users
 * - Markdown rendering support for rich descriptions
 */
export const StatusCard: React.FC<StatusCardProps> = ({
  status,
  title,
  description,
  actions,
  details,
}) => {
  const config = statusConfig[status];

  const IconComponent = config.icon;

  return (
    <Box
      bg={config.bg}
      borderLeft="6px solid"
      borderLeftColor={config.borderColor}
      borderRadius="xl"
      p={{ base: 5, md: 6 }}
      role="status"
      aria-live="polite"
    >
      <VStack align="stretch" gap={4}>
        <HStack gap={4} align="start">
          <IconComponent
            size={32}
            color={config.iconColor}
            style={{ flexShrink: 0 }}
          />
          <VStack align="start" gap={3} flex="1">
            <Heading
              as="h3"
              fontSize={{ base: "sm", md: "md" }}
              fontWeight="600"
              color="fg.emphasis"
              letterSpacing="-0.02em"
              lineHeight="1.3"
            >
              {title}
            </Heading>
            <MarkdownRenderer
              content={description}
              fontSize={{ base: "sm", md: "md" }}
            />
          </VStack>
        </HStack>

        {details && <Box pt={2}>{details}</Box>}

        {actions && <Box pt={2}>{actions}</Box>}
      </VStack>
    </Box>
  );
};
