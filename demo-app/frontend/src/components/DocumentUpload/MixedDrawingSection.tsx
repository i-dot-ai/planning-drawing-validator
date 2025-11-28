import React from "react";
import { Box, VStack, Flex, Text, Badge } from "@chakra-ui/react";
import { IndividualDrawing } from "../../types";
import { RequirementItem } from "./RequirementItem";
import { MarkdownRenderer } from "../ui/MarkdownRenderer";
import { formatDocumentType, getValidityConfig } from "../../utils/format";

interface MixedDrawingSectionProps {
  drawing: IndividualDrawing;
}

/**
 * MixedDrawingSection displays validation results for a single drawing within a mixed drawing file
 *
 * Mixed drawings contain multiple types (e.g., floor plan + elevations in one PDF)
 * Each constituent drawing is validated separately
 */
export const MixedDrawingSection: React.FC<MixedDrawingSectionProps> = ({
  drawing,
}) => {
  const validityConfig = getValidityConfig(drawing.validity);

  return (
    <Box
      borderRadius="xl"
      borderWidth="1px"
      borderColor="rgba(79, 134, 113, 0.24)"
      bg="rgba(236, 245, 240, 0.4)"
      p={{ base: 4, md: 5 }}
    >
      <VStack align="stretch" gap={4}>
        {/* Header with drawing type and status */}
        <Flex justify="space-between" align="center" gap={3} flexWrap="wrap">
          <Text
            fontWeight="700"
            fontSize={{ base: "md", md: "lg" }}
            color="fg.emphasis"
          >
            {formatDocumentType(drawing.drawing_type)}
          </Text>
          <Badge
            px={3}
            py={1}
            borderRadius="full"
            bg={validityConfig.badgeBg}
            color={validityConfig.badgeColor}
            fontSize="sm"
            fontWeight="600"
          >
            {validityConfig.label}
          </Badge>
        </Flex>

        {/* Reasoning */}
        {drawing.reasoning && (
          <MarkdownRenderer
            content={drawing.reasoning}
            fontSize={{ base: "sm", md: "md" }}
            compact
          />
        )}

        {/* Confidence level */}
        {drawing.confidence && (
          <Flex gap={2} align="center">
            <Text fontSize="sm" color="fg.muted">
              Confidence:
            </Text>
            <Text fontSize="sm" color="fg.emphasis" fontWeight="500">
              {drawing.confidence.charAt(0) +
                drawing.confidence.slice(1).toLowerCase()}
            </Text>
          </Flex>
        )}

        {/* Requirements */}
        {drawing.requirements_checked &&
          drawing.requirements_checked.length > 0 && (
            <VStack align="stretch" gap={3} pt={2}>
              <Text
                fontSize="sm"
                fontWeight="600"
                color="fg.emphasis"
                textTransform="uppercase"
                letterSpacing="0.05em"
              >
                Requirements
              </Text>
              {drawing.requirements_checked.map((req, index) => (
                <RequirementItem
                  key={`${drawing.drawing_type}-req-${index}`}
                  requirement={req}
                />
              ))}
            </VStack>
          )}
      </VStack>
    </Box>
  );
};
