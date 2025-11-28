import React, { memo } from "react";
import { VStack, HStack, Box, Text, Icon, Flex } from "@chakra-ui/react";
import { Upload, Tag, Play, CheckCircle2 } from "lucide-react";
import { presets } from "@/lib/design-tokens";

interface GettingStartedProps {
  hasDocuments: boolean;
  hasLabels: boolean;
}

interface StepProps {
  number: number;
  title: string;
  description: string;
  icon: React.ElementType;
  isComplete: boolean;
  isActive: boolean;
}

const Step = memo(function Step({
  number,
  title,
  description,
  icon: IconComponent,
  isComplete,
  isActive,
}: StepProps) {
  return (
    <Flex
      align="flex-start"
      gap={4}
      p={4}
      borderRadius="lg"
      border="1px solid"
      borderColor={isActive ? "gray.300" : "gray.200"}
      bg={isComplete ? "gray.50" : "white"}
      opacity={isComplete ? 0.7 : 1}
      transition="all 0.15s ease"
      w="full"
    >
      {/* Step indicator */}
      <Flex
        align="center"
        justify="center"
        boxSize={10}
        borderRadius="full"
        bg={isComplete ? "gray.900" : isActive ? "gray.100" : "gray.50"}
        color={isComplete ? "white" : isActive ? "gray.900" : "gray.400"}
        flexShrink={0}
      >
        {isComplete ? (
          <Icon as={CheckCircle2} boxSize={5} />
        ) : (
          <Icon as={IconComponent} boxSize={5} />
        )}
      </Flex>

      {/* Content */}
      <VStack align="start" gap={0.5} flex={1}>
        <HStack gap={2}>
          <Text
            fontSize="xs"
            fontWeight="semibold"
            color={isComplete ? "gray.500" : "gray.400"}
          >
            STEP {number}
          </Text>
          {isComplete && (
            <Text fontSize="xs" color="gray.500">
              ✓ Complete
            </Text>
          )}
        </HStack>
        <Text
          fontSize="md"
          fontWeight="semibold"
          color={isComplete ? "gray.500" : "gray.900"}
        >
          {title}
        </Text>
        <Text fontSize="sm" color="gray.500">
          {description}
        </Text>
      </VStack>
    </Flex>
  );
});

export const GettingStarted = memo(function GettingStarted({
  hasDocuments,
  hasLabels,
}: GettingStartedProps) {
  const isReadyToRun = hasDocuments;
  const allComplete = hasDocuments && hasLabels;

  // If everything is configured, show minimal ready state
  if (allComplete) {
    return (
      <Box
        p={6}
        borderRadius="lg"
        border="1px solid"
        borderColor="gray.200"
        bg="white"
        textAlign="center"
      >
        <VStack gap={3}>
          <Flex
            align="center"
            justify="center"
            boxSize={12}
            borderRadius="full"
            bg="gray.900"
            color="white"
          >
            <Icon as={Play} boxSize={5} />
          </Flex>
          <VStack gap={1}>
            <Text fontSize="lg" fontWeight="semibold" color="gray.900">
              Ready to evaluate
            </Text>
            <Text fontSize="sm" color="gray.500">
              Click <strong>Run</strong> in the header to start processing your
              documents.
            </Text>
          </VStack>
        </VStack>
      </Box>
    );
  }

  return (
    <VStack gap={6} align="stretch">
      {/* Header */}
      <VStack gap={2} align="start">
        <Text {...presets.sectionLabel}>Getting Started</Text>
        <Text fontSize="md" color="gray.600">
          Set up your evaluation by completing the steps below.
        </Text>
      </VStack>

      {/* Steps */}
      <VStack gap={3} align="stretch">
        <Step
          number={1}
          title="Upload documents"
          description="Click the Upload button in the header to add PDF or image files."
          icon={Upload}
          isComplete={hasDocuments}
          isActive={!hasDocuments}
        />

        <Step
          number={2}
          title="Add labels (optional)"
          description="Click Labels in the header to provide ground truth for accuracy measurement."
          icon={Tag}
          isComplete={hasLabels}
          isActive={hasDocuments && !hasLabels}
        />

        <Step
          number={3}
          title="Run evaluation"
          description="Click Run to process documents through the validation pipeline."
          icon={Play}
          isComplete={false}
          isActive={isReadyToRun}
        />
      </VStack>

      {/* Tip */}
      <Box
        p={4}
        borderRadius="lg"
        bg="gray.50"
        border="1px solid"
        borderColor="gray.100"
      >
        <Text fontSize="sm" color="gray.600">
          <strong>Tip:</strong> Labels are optional but recommended. They enable
          accuracy metrics, reasoning evaluation, and help you understand how
          well the model performs on your specific documents.
        </Text>
      </Box>
    </VStack>
  );
});

export default GettingStarted;
