import React from "react";
import { Box, Flex, Text, Badge } from "@chakra-ui/react";
import { Requirement } from "../../types";

interface RequirementItemProps {
  requirement: Requirement;
}

/**
 * RequirementItem displays a single planning requirement with its validation status.
 *
 * Supports three states: Pass (green), Fail (red), and Needs Review (amber).
 * Uses WCAG AA compliant colours and clear status labels.
 */
export const RequirementItem: React.FC<RequirementItemProps> = ({
  requirement,
}) => {
  const getStatusConfig = (status: string) => {
    switch (status.toUpperCase()) {
      case "PASS":
        return {
          bg: "rgba(59, 127, 115, 0.16)",
          color: "rgba(44, 124, 91, 1)",
          label: "Pass",
        };
      case "FAIL":
        return {
          bg: "rgba(201, 86, 76, 0.16)",
          color: "rgba(156, 41, 34, 1)",
          label: "Fail",
        };
      case "NEEDS_REVIEW":
      case "CLARIFICATION_NEEDED":
        return {
          bg: "rgba(203, 162, 61, 0.16)",
          color: "rgba(124, 76, 20, 1)",
          label: "Needs review",
        };
      default:
        return {
          bg: "rgba(128, 128, 128, 0.16)",
          color: "rgba(64, 64, 64, 1)",
          label: status,
        };
    }
  };

  const statusConfig = getStatusConfig(requirement.status);

  return (
    <Box
      borderRadius="lg"
      borderWidth="1px"
      borderColor={
        requirement.status === "PASS"
          ? "rgba(59, 127, 115, 0.24)"
          : requirement.status === "FAIL"
            ? "rgba(201, 86, 76, 0.24)"
            : "rgba(203, 162, 61, 0.24)"
      }
      bg={
        requirement.status === "PASS"
          ? "rgba(59, 127, 115, 0.04)"
          : requirement.status === "FAIL"
            ? "rgba(201, 86, 76, 0.04)"
            : "rgba(203, 162, 61, 0.04)"
      }
      p={{ base: 3, md: 4 }}
    >
      <Flex
        justify="space-between"
        align="flex-start"
        gap={3}
        flexWrap="wrap"
        mb={requirement.details ? 2 : 0}
      >
        <Text
          color="fg.emphasis"
          fontWeight="600"
          fontSize={{ base: "sm", md: "md" }}
          flex="1"
          minW="0"
          wordBreak="break-word"
        >
          {requirement.requirement}
        </Text>
        <Badge
          px={3}
          py={1}
          borderRadius="full"
          bg={statusConfig.bg}
          color={statusConfig.color}
          fontSize="xs"
          fontWeight="600"
          flexShrink={0}
        >
          {statusConfig.label}
        </Badge>
      </Flex>
      {requirement.details && (
        <Text
          fontSize="sm"
          color="fg.muted"
          mt={2}
          lineHeight="1.6"
          wordBreak="break-word"
        >
          {requirement.details}
        </Text>
      )}
    </Box>
  );
};
