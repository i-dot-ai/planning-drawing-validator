import React, { memo } from "react";
import { VStack, Icon, Heading, Text, Button, Box } from "@chakra-ui/react";
import { FileQuestion, Search, History } from "lucide-react";

interface EmptyStateProps {
  variant: "no-evaluations" | "no-results" | "no-history";
  searchQuery?: string;
  onAction?: () => void;
}

export const EmptyState = memo(function EmptyState({
  variant,
  searchQuery,
  onAction,
}: EmptyStateProps) {
  const configs = {
    "no-evaluations": {
      icon: FileQuestion,
      title: "No documents processed yet",
      description: "Configure and start a run to process planning documents.",
      actionLabel: null,
    },
    "no-results": {
      icon: Search,
      title: "No matching documents",
      description: `No documents match your search query "${searchQuery}".`,
      actionLabel: null,
    },
    "no-history": {
      icon: History,
      title: "No processing runs yet",
      description:
        "Start processing documents to see your results history here.",
      actionLabel: "Go to Live",
    },
  };

  const config = configs[variant];
  const IconComponent = config.icon;

  return (
    <VStack gap={4} py={20} textAlign="center">
      <Box p={4} borderRadius="lg" bg="bg.muted">
        <Icon as={IconComponent} boxSize={10} color="fg.subtle" />
      </Box>
      <VStack gap={2}>
        <Heading size="md">{config.title}</Heading>
        <Text fontSize="md" color="fg.muted" maxW="md">
          {config.description}
        </Text>
      </VStack>
      {config.actionLabel && onAction && (
        <Button onClick={onAction} size="sm" variant="solid" mt={2}>
          {config.actionLabel}
        </Button>
      )}
    </VStack>
  );
});
