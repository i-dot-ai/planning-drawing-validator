import React, { memo } from "react";
import { Box, Flex, HStack, Text } from "@chakra-ui/react";
import { SimpleTooltip } from "@/lib/chakra-compat";

interface ReadyDocument {
  document_id: string;
  filename: string;
  hasLabel?: boolean;
}

interface ReadyQueueProps {
  documents: ReadyDocument[];
  labelCount: number;
}

const Dot = memo(
  ({ doc, hasLabel }: { doc: ReadyDocument; hasLabel: boolean }) => {
    return (
      <SimpleTooltip label={doc.filename}>
        <Box
          w="6px"
          h="6px"
          borderRadius="full"
          bg={hasLabel ? "green.400" : "gray.200"}
          flexShrink={0}
          transition="all 0.2s ease"
          cursor="default"
          _hover={{
            transform: "scale(1.5)",
          }}
        />
      </SimpleTooltip>
    );
  },
);

Dot.displayName = "ReadyDot";

export const ReadyQueue = memo<ReadyQueueProps>(function ReadyQueue({
  documents,
  labelCount,
}) {
  if (documents.length === 0) return null;

  const labeledCount = labelCount;
  const unlabeledCount = Math.max(0, documents.length - labelCount);

  return (
    <Box
      bg="white"
      borderRadius="lg"
      border="1px solid"
      borderColor="gray.200"
      p={5}
    >
      {/* Minimal header with counts */}
      <Flex align="center" justify="space-between" mb={4}>
        <HStack gap={4}>
          <HStack gap={1.5}>
            <Box w="6px" h="6px" borderRadius="full" bg="gray.200" />
            <Text fontSize="xs" color="gray.400" fontWeight="medium">
              {documents.length} ready
            </Text>
          </HStack>
        </HStack>

        <HStack gap={4}>
          {labeledCount > 0 && (
            <HStack gap={1.5}>
              <Box w="6px" h="6px" borderRadius="full" bg="green.400" />
              <Text fontSize="xs" color="gray.400" fontWeight="medium">
                {labeledCount} labeled
              </Text>
            </HStack>
          )}
          {unlabeledCount > 0 && labelCount > 0 && (
            <HStack gap={1.5}>
              <Box
                w="6px"
                h="6px"
                borderRadius="full"
                bg="gray.200"
                border="1px solid"
                borderColor="gray.300"
              />
              <Text fontSize="xs" color="gray.400" fontWeight="medium">
                {unlabeledCount} unlabeled
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
        {documents.map((doc, index) => (
          <Dot key={doc.document_id} doc={doc} hasLabel={index < labelCount} />
        ))}
      </Box>

      <Text fontSize="xs" color="gray.400" mt={4} textAlign="center">
        Press Run to start
      </Text>
    </Box>
  );
});
