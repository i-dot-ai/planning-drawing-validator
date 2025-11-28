import React from "react";
import { Box, Badge, Heading, Text, HStack, Flex } from "@chakra-ui/react";
import { DocumentUpload as DocumentUploadType } from "../../types";
import { MarkdownRenderer } from "../ui/MarkdownRenderer";
import {
  formatFileSize,
  formatDocumentType,
  getValidityConfig,
} from "../../utils/format";

interface UploadCardProps {
  upload: DocumentUploadType;
  isActive: boolean;
  onClick: () => void;
  onKeyDown: (event: React.KeyboardEvent) => void;
  cardRef?: (element: HTMLDivElement | null) => void;
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case "uploading":
      return (
        <Badge
          px={2}
          py={0.5}
          borderRadius="full"
          bg="rgba(79, 134, 113, 0.16)"
          color="rgba(79, 134, 113, 1)"
          fontSize="2xs"
        >
          Uploading
        </Badge>
      );
    case "validating":
      return (
        <Badge
          px={2}
          py={0.5}
          borderRadius="full"
          bg="rgba(203, 162, 61, 0.16)"
          color="rgba(124, 76, 20, 1)"
          fontSize="2xs"
        >
          Analysing
        </Badge>
      );
    case "complete":
      return (
        <Badge
          px={2}
          py={0.5}
          borderRadius="full"
          bg="rgba(59, 127, 115, 0.16)"
          color="rgba(44, 124, 91, 1)"
          fontSize="2xs"
        >
          Complete
        </Badge>
      );
    case "error":
      return (
        <Badge
          px={2}
          py={0.5}
          borderRadius="full"
          bg="rgba(201, 86, 76, 0.16)"
          color="rgba(156, 41, 34, 1)"
          fontSize="2xs"
        >
          Error
        </Badge>
      );
    default:
      return null;
  }
};

const getRequirementStats = (result?: DocumentUploadType["result"]) => {
  if (!result?.requirements_checked?.length) {
    return { passed: 0, total: 0 };
  }

  const passed = result.requirements_checked.filter(
    (req) => req.status === "PASS",
  ).length;
  const total = result.requirements_checked.length;

  return { passed, total };
};

const getUserFriendlyMessage = (upload: DocumentUploadType): string => {
  const { status, result } = upload;

  if (status.status === "uploading") {
    return "Uploading your drawing...";
  }

  if (status.status === "validating") {
    return "Analysing your drawing...";
  }

  if (status.status === "complete" && result?.reasoning) {
    return result.reasoning.length > 90
      ? `${result.reasoning.slice(0, 87)}…`
      : result.reasoning;
  }

  if (status.status === "error" && status.message) {
    return "Could not analyse this drawing";
  }

  return "Processing...";
};

export const UploadCard: React.FC<UploadCardProps> = ({
  upload,
  isActive,
  onClick,
  onKeyDown,
  cardRef,
}) => {
  const isComplete = upload.status.status === "complete";
  const isError = upload.status.status === "error";
  const validityConfig = upload.result
    ? getValidityConfig(upload.result.validity)
    : undefined;
  const { passed, total } = getRequirementStats(upload.result);
  const checksLabel = total > 0 ? `${passed}/${total} checks` : undefined;
  const message = getUserFriendlyMessage(upload);

  return (
    <Box
      ref={cardRef}
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={onKeyDown}
      borderRadius="2xl"
      borderWidth={isActive ? "2px" : "1px"}
      borderColor={
        isActive ? "rgba(79, 134, 113, 0.48)" : "rgba(79, 134, 113, 0.24)"
      }
      bg={isActive ? "rgba(236, 245, 240, 0.85)" : "rgba(236, 245, 240, 0.64)"}
      boxShadow="none"
      w="100%"
      minH={{ base: "200px", md: "220px" }}
      px={{ base: 4, md: 5 }}
      py={{ base: 4, md: 5 }}
      cursor="pointer"
      transition="all 0.2s ease"
      _focus={{
        outline: "2px solid rgba(79, 134, 113, 0.45)",
        outlineOffset: "2px",
      }}
      _hover={{
        transform: "translateY(-2px)",
        borderColor: "rgba(79, 134, 113, 0.48)",
      }}
      aria-label={`Upload card for ${upload.file.name}`}
    >
      <Flex direction="column" h="100%" gap={3}>
        {/* Status row */}
        <Flex align="center" justify="space-between" gap={2}>
          <HStack gap={2} align="center">
            <Box>{getStatusBadge(upload.status.status)}</Box>
            {isError && (
              <Text fontSize="xs" color="error.700" fontWeight="500">
                Check failed
              </Text>
            )}
          </HStack>
          {isComplete && validityConfig && (
            <Badge
              px={3}
              py={1}
              borderRadius="full"
              bg={validityConfig.badgeBg}
              color={validityConfig.badgeColor}
              fontSize="xs"
              letterSpacing="0.02em"
              fontWeight="600"
            >
              {validityConfig.label}
            </Badge>
          )}
        </Flex>

        {/* File name */}
        <Box>
          <Heading
            as="h3"
            fontSize={{ base: "md", md: "lg" }}
            letterSpacing="-0.01em"
            fontWeight="600"
            lineClamp={2}
            wordBreak="break-word"
          >
            {upload.file.name}
          </Heading>
          <HStack gap={2} fontSize="sm" color="fg.muted" mt={1} flexWrap="wrap">
            <Text>{formatFileSize(upload.file.size)}</Text>
            {isComplete && upload.result?.document_type && (
              <>
                <Text>•</Text>
                <Text>{formatDocumentType(upload.result.document_type)}</Text>
              </>
            )}
          </HStack>
        </Box>

        {/* Message or stats */}
        <Box
          flex="1"
          display="flex"
          flexDirection="column"
          justifyContent="flex-end"
        >
          {checksLabel && isComplete && (
            <Badge
              alignSelf="flex-start"
              px={2.5}
              py={1}
              borderRadius="full"
              bg="rgba(79, 134, 113, 0.12)"
              color="brand.700"
              fontSize="xs"
              mb={2}
            >
              {checksLabel}
            </Badge>
          )}
          <Box
            fontSize="sm"
            color="fg.muted"
            style={{
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical" as const,
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {isComplete && upload.result?.reasoning ? (
              <MarkdownRenderer content={message} fontSize="sm" compact />
            ) : (
              <Text fontSize="sm" color="fg.muted">
                {message}
              </Text>
            )}
          </Box>
        </Box>
      </Flex>
    </Box>
  );
};
