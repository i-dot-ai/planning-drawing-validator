import React, { memo } from "react";
import { Box, Flex, HStack, Text, Tooltip, Portal } from "@chakra-ui/react";
import { keyframes } from "@emotion/react";

export interface QueuedDocument {
  document_id: string;
  filename: string;
  status: "pending" | "processing" | "completed" | "error";
}

interface DocumentQueueProps {
  documents: QueuedDocument[];
  className?: string;
}

// Subtle pulse animation for processing dots
const pulse = keyframes`
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.85);
  }
`;

// Gentle fade-in for completed dots
const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
`;

interface DotProps {
  doc: QueuedDocument;
}

const Dot = memo(({ doc }: DotProps) => {
  const getStyles = (status: QueuedDocument["status"]) => {
    switch (status) {
      case "pending":
        return {
          bg: "gray.200",
          size: "6px",
          animation: undefined,
        };
      case "processing":
        return {
          bg: "gray.900",
          size: "8px",
          animation: `${pulse} 1.5s ease-in-out infinite`,
        };
      case "completed":
        return {
          bg: "green.400",
          size: "6px",
          animation: `${fadeIn} 0.3s ease-out`,
        };
      case "error":
        return {
          bg: "red.400",
          size: "6px",
          animation: `${fadeIn} 0.3s ease-out`,
        };
    }
  };

  const styles = getStyles(doc.status);

  return (
    <Tooltip.Root openDelay={200}>
      <Tooltip.Trigger asChild>
        <Box
          w={styles.size}
          h={styles.size}
          borderRadius="full"
          bg={styles.bg}
          flexShrink={0}
          transition="all 0.2s ease"
          animation={styles.animation}
          cursor="default"
          _hover={{
            transform: doc.status === "processing" ? undefined : "scale(1.5)",
          }}
        />
      </Tooltip.Trigger>
      <Portal>
        <Tooltip.Positioner>
          <Tooltip.Content
            bg="gray.900"
            color="white"
            fontSize="xs"
            px={2}
            py={1}
            borderRadius="md"
          >
            {doc.filename}
          </Tooltip.Content>
        </Tooltip.Positioner>
      </Portal>
    </Tooltip.Root>
  );
});

Dot.displayName = "Dot";

export const DocumentQueue = memo<DocumentQueueProps>(
  function DocumentQueue({ documents, className }: DocumentQueueProps) {
    if (documents.length === 0) return null;

    const pending = documents.filter((d) => d.status === "pending");
    const processing = documents.filter((d) => d.status === "processing");
    const completed = documents.filter((d) => d.status === "completed");
    const error = documents.filter((d) => d.status === "error");

    // Hide if nothing is pending or processing
    if (pending.length === 0 && processing.length === 0) return null;

    // Sort: processing first, then pending
    const sortedDocs = [...processing, ...pending];

    return (
      <Box
        className={className}
        bg="white"
        borderRadius="lg"
        border="1px solid"
        borderColor="gray.200"
        p={5}
      >
        {/* Minimal header with counts */}
        <Flex align="center" justify="space-between" mb={4}>
          <HStack gap={4}>
            {processing.length > 0 && (
              <HStack gap={1.5}>
                <Box
                  w="8px"
                  h="8px"
                  borderRadius="full"
                  bg="gray.900"
                  animation={`${pulse} 1.5s ease-in-out infinite`}
                />
                <Text fontSize="xs" color="gray.500" fontWeight="medium">
                  {processing.length}
                </Text>
              </HStack>
            )}
            {pending.length > 0 && (
              <HStack gap={1.5}>
                <Box w="6px" h="6px" borderRadius="full" bg="gray.200" />
                <Text fontSize="xs" color="gray.400" fontWeight="medium">
                  {pending.length}
                </Text>
              </HStack>
            )}
          </HStack>

          <HStack gap={4}>
            {completed.length > 0 && (
              <HStack gap={1.5}>
                <Box w="6px" h="6px" borderRadius="full" bg="green.400" />
                <Text fontSize="xs" color="gray.400" fontWeight="medium">
                  {completed.length}
                </Text>
              </HStack>
            )}
            {error.length > 0 && (
              <HStack gap={1.5}>
                <Box w="6px" h="6px" borderRadius="full" bg="red.400" />
                <Text fontSize="xs" color="gray.400" fontWeight="medium">
                  {error.length}
                </Text>
              </HStack>
            )}
          </HStack>
        </Flex>

        {/* Dot grid - fills available width */}
        <Box
          display="grid"
          gridTemplateColumns="repeat(auto-fill, minmax(8px, 1fr))"
          gap="6px"
          justifyItems="center"
          alignItems="center"
          maxH="140px"
          overflowY="auto"
          css={{
            "&::-webkit-scrollbar": {
              width: "4px",
            },
            "&::-webkit-scrollbar-track": {
              background: "transparent",
            },
            "&::-webkit-scrollbar-thumb": {
              background: "#E2E8F0",
              borderRadius: "2px",
            },
          }}
        >
          {sortedDocs.map((doc) => (
            <Dot key={doc.document_id} doc={doc} />
          ))}
        </Box>
      </Box>
    );
  },
  (prevProps, nextProps) => {
    if (prevProps.documents.length !== nextProps.documents.length) {
      return false;
    }
    for (let i = 0; i < prevProps.documents.length; i++) {
      const prev = prevProps.documents[i];
      const next = nextProps.documents[i];
      if (
        prev.document_id !== next.document_id ||
        prev.status !== next.status
      ) {
        return false;
      }
    }
    return true;
  },
);
