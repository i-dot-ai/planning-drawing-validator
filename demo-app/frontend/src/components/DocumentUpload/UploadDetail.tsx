import React from "react";
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Accordion,
  Flex,
  Badge,
} from "@chakra-ui/react";
import { FileText, Clock, Sparkles, Brain, ChevronDown } from "lucide-react";
import { DocumentUpload as DocumentUploadType } from "../../types";
import { StatusCard } from "../ui/StatusCard";
import { StageIndicator } from "./StageIndicator";
import { RequirementItem } from "./RequirementItem";
import { MixedDrawingSection } from "./MixedDrawingSection";
import { MarkdownRenderer } from "../ui/MarkdownRenderer";
import { formatFileSize, formatDocumentType } from "../../utils/format";

interface UploadDetailProps {
  upload: DocumentUploadType;
  onPreview?: (upload: DocumentUploadType) => void;
}

/**
 * UploadDetail displays comprehensive validation results for a selected upload.
 *
 * Shows status, document classification, requirement checks, and optional
 * extended thinking analysis. Technical details use progressive disclosure
 * (collapsed by default) for a cleaner interface.
 */
export const UploadDetail: React.FC<UploadDetailProps> = ({
  upload,
  onPreview,
}) => {
  const isProcessing =
    upload.status.status === "uploading" ||
    upload.status.status === "validating";
  const isComplete = upload.status.status === "complete";
  const isError = upload.status.status === "error";

  const getProcessingMessage = () => {
    if (upload.status.status === "uploading") {
      return "Uploading your drawing...";
    }
    if (upload.status.status === "validating") {
      return "Analysing your drawing...";
    }
    return "Processing...";
  };

  // Get status card configuration
  const getStatusConfig = () => {
    if (isError) {
      return {
        status: "error" as const,
        title: "Analysis failed",
        description:
          upload.status.message ||
          "We could not analyse this drawing. Please try again or contact support.",
      };
    }

    if (!upload.result) {
      return null;
    }

    const validity = upload.result.validity.toUpperCase();

    switch (validity) {
      case "VALID":
        return {
          status: "success" as const,
          title: "Valid - Ready to submit",
          description:
            upload.result.reasoning ||
            "All planning requirements have been met for this drawing.",
        };
      case "INVALID":
        return {
          status: "error" as const,
          title: "Invalid - Requires changes",
          description:
            upload.result.reasoning ||
            "Some planning requirements have not been met. Please review the issues below.",
        };
      case "CLARIFICATION_NEEDED":
        return {
          status: "warning" as const,
          title: "Needs review",
          description:
            upload.result.reasoning ||
            "Some requirements could not be automatically verified and need manual review.",
        };
      default:
        return {
          status: "info" as const,
          title: "Analysis complete",
          description: upload.result.reasoning || "Review the results below.",
        };
    }
  };

  const statusConfig = getStatusConfig();

  const handlePreview = () => {
    if (onPreview) {
      onPreview(upload);
    }
  };

  return (
    <VStack
      align="stretch"
      gap={6}
      bg="rgba(255, 255, 255, 0.95)"
      borderRadius="2xl"
      borderWidth="1px"
      borderColor="rgba(79, 134, 113, 0.24)"
      p={{ base: 5, md: 6 }}
      role="region"
      aria-label="Upload details"
    >
      {/* File header */}
      <VStack align="stretch" gap={2}>
        <Text
          fontSize={{ base: "lg", md: "xl" }}
          fontWeight="700"
          color="fg.emphasis"
          wordBreak="break-word"
        >
          {upload.file.name}
        </Text>
        <HStack gap={3} fontSize="sm" color="fg.muted" flexWrap="wrap">
          <Text>{formatFileSize(upload.file.size)}</Text>
          {isComplete && upload.result?.document_type && (
            <>
              <Text>•</Text>
              <Text>{formatDocumentType(upload.result.document_type)}</Text>
            </>
          )}
          {isComplete && upload.result?.execution_time && (
            <>
              <Text>•</Text>
              <HStack gap={1}>
                <Clock size={14} />
                <Text>
                  Processed in {upload.result.execution_time.toFixed(1)}s
                </Text>
              </HStack>
            </>
          )}
        </HStack>
      </VStack>

      {/* Processing status */}
      {isProcessing && (
        <StageIndicator
          status={upload.status.status}
          message={getProcessingMessage()}
        />
      )}

      {/* Results status card */}
      {isComplete && statusConfig && (
        <StatusCard
          status={statusConfig.status}
          title={statusConfig.title}
          description={statusConfig.description}
          actions={
            <HStack gap={3} flexWrap="wrap">
              <Button size="md" variant="solid" onClick={handlePreview}>
                <FileText size={16} />
                View document
              </Button>
            </HStack>
          }
        />
      )}

      {/* Error status card */}
      {isError && statusConfig && (
        <StatusCard
          status={statusConfig.status}
          title={statusConfig.title}
          description={statusConfig.description}
        />
      )}

      {/* Thinking section - collapsible when available */}
      {isComplete &&
        upload.result &&
        (upload.result.classification_thinking ||
          upload.result.validation_thinking) && (
          <Accordion.Root collapsible>
            <Accordion.Item
              value="thinking"
              border="none"
              bg="rgba(79, 134, 113, 0.06)"
              borderRadius="xl"
            >
              <Accordion.ItemTrigger
                px={5}
                py={4}
                _hover={{ bg: "rgba(79, 134, 113, 0.12)" }}
                borderRadius="xl"
              >
                <HStack flex="1" gap={3}>
                  <Brain size={20} color="var(--chakra-colors-brand-600)" />
                  <Text fontSize="md" fontWeight="600" color="fg.emphasis">
                    AI Reasoning Process
                  </Text>
                  <Badge
                    ml={2}
                    px={2}
                    py={0.5}
                    borderRadius="full"
                    bg="brand.600"
                    color="white"
                    fontSize="2xs"
                  >
                    Gemini Thinking
                  </Badge>
                </HStack>
                <Accordion.ItemIndicator>
                  <ChevronDown
                    size={20}
                    color="var(--chakra-colors-brand-600)"
                  />
                </Accordion.ItemIndicator>
              </Accordion.ItemTrigger>
              <Accordion.ItemContent px={5} pb={4}>
                <VStack align="stretch" gap={4}>
                  {upload.result.classification_thinking && (
                    <Box>
                      <Text
                        fontSize="sm"
                        fontWeight="600"
                        color="brand.700"
                        mb={2}
                        textTransform="uppercase"
                        letterSpacing="0.05em"
                      >
                        Classification Thinking
                      </Text>
                      <Box
                        p={4}
                        bg="rgba(255, 255, 255, 0.8)"
                        borderRadius="lg"
                        borderLeft="3px solid"
                        borderLeftColor="brand.400"
                      >
                        <MarkdownRenderer
                          content={upload.result.classification_thinking}
                          fontSize="sm"
                        />
                      </Box>
                    </Box>
                  )}
                  {upload.result.validation_thinking && (
                    <Box>
                      <Text
                        fontSize="sm"
                        fontWeight="600"
                        color="brand.700"
                        mb={2}
                        textTransform="uppercase"
                        letterSpacing="0.05em"
                      >
                        Validation Thinking
                      </Text>
                      <Box
                        p={4}
                        bg="rgba(255, 255, 255, 0.8)"
                        borderRadius="lg"
                        borderLeft="3px solid"
                        borderLeftColor="brand.400"
                      >
                        <MarkdownRenderer
                          content={upload.result.validation_thinking}
                          fontSize="sm"
                        />
                      </Box>
                    </Box>
                  )}
                </VStack>
              </Accordion.ItemContent>
            </Accordion.Item>
          </Accordion.Root>
        )}

      {/* Requirements section - always visible when complete */}
      {isComplete && upload.result && (
        <VStack align="stretch" gap={4}>
          <Flex justify="space-between" align="center">
            <Text
              fontSize="md"
              fontWeight="600"
              color="fg.emphasis"
              textTransform="uppercase"
              letterSpacing="0.05em"
            >
              {upload.result.is_mixed_drawing
                ? "Individual Drawings"
                : "Requirements"}
            </Text>
            {upload.result.confidence && (
              <Badge
                px={3}
                py={1}
                borderRadius="full"
                bg="rgba(79, 134, 113, 0.12)"
                color="brand.700"
                fontSize="xs"
              >
                {upload.result.confidence.charAt(0) +
                  upload.result.confidence.slice(1).toLowerCase()}{" "}
                confidence
              </Badge>
            )}
          </Flex>

          {/* Mixed drawing sections */}
          {upload.result.is_mixed_drawing &&
          upload.result.constituent_drawings?.length ? (
            <VStack align="stretch" gap={4}>
              {upload.result.constituent_drawings.map((drawing, index) => (
                <MixedDrawingSection
                  key={`drawing-${index}`}
                  drawing={drawing}
                />
              ))}
            </VStack>
          ) : (
            /* Single drawing requirements */
            <VStack align="stretch" gap={3}>
              {upload.result.requirements_checked?.map((req, index) => (
                <RequirementItem key={`req-${index}`} requirement={req} />
              ))}
            </VStack>
          )}
        </VStack>
      )}

      {/* Technical details (collapsed by default) */}
      {isComplete && upload.result && (
        <Accordion.Root collapsible>
          <Accordion.Item value="technical" border="none">
            <Accordion.ItemTrigger px={0} _hover={{ bg: "transparent" }}>
              <Flex flex="1" justify="space-between" align="center">
                <HStack gap={2}>
                  <Sparkles size={16} color="var(--chakra-colors-brand-600)" />
                  <Text fontSize="sm" fontWeight="500" color="fg.muted">
                    Technical details
                  </Text>
                </HStack>
                <Accordion.ItemIndicator>
                  <ChevronDown size={16} />
                </Accordion.ItemIndicator>
              </Flex>
            </Accordion.ItemTrigger>
            <Accordion.ItemContent px={0} pb={0} pt={3}>
              <VStack align="stretch" gap={3} fontSize="sm">
                <Box>
                  <Text color="fg.muted" mb={1}>
                    Document ID
                  </Text>
                  <Text
                    color="fg.emphasis"
                    fontFamily="mono"
                    fontSize="xs"
                    wordBreak="break-all"
                  >
                    {upload.result.document_id}
                  </Text>
                </Box>
                {upload.result.prompt_type && (
                  <Box>
                    <Text color="fg.muted" mb={1}>
                      Validation prompt
                    </Text>
                    <Text color="fg.emphasis" fontFamily="mono" fontSize="xs">
                      {upload.result.prompt_type}
                    </Text>
                  </Box>
                )}
                <Box>
                  <Text color="fg.muted" mb={1}>
                    Classification confidence
                  </Text>
                  <Text color="fg.emphasis">
                    {upload.result.confidence.charAt(0) +
                      upload.result.confidence.slice(1).toLowerCase()}
                  </Text>
                </Box>
              </VStack>
            </Accordion.ItemContent>
          </Accordion.Item>
        </Accordion.Root>
      )}
    </VStack>
  );
};
