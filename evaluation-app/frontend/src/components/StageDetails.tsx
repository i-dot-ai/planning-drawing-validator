import React, { memo, useState } from "react";
import {
  Box,
  VStack,
  HStack,
  Flex,
  Text,
  Badge,
  Icon,
  Card,
  Separator,
  Collapsible,
} from "@chakra-ui/react";
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  Circle,
  ChevronRight,
  FileText,
  Code,
  XCircle,
} from "lucide-react";
import { EvaluationStage, ConstituentValidation } from "../types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface StageDetailsProps {
  stages: EvaluationStage[];
}

export const StageDetails = memo(function StageDetails({
  stages,
}: StageDetailsProps) {
  return (
    <VStack gap={3} align="stretch">
      {stages.map((stage, index) => (
        <StageCard
          key={stage.stage}
          stage={stage}
          isLast={index === stages.length - 1}
        />
      ))}
    </VStack>
  );
});

interface StageCardProps {
  stage: EvaluationStage;
  isLast: boolean;
}

const StageCard = memo(function StageCard({ stage, isLast }: StageCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showRawPrompt, setShowRawPrompt] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(["output", "reasoning_confidence", "json"]),
  );

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  const statusConfig = {
    completed: {
      icon: CheckCircle2,
      iconColor: "gray.600",
      iconBg: "gray.100",
      headerBg: "white",
      borderColor: "gray.200",
    },
    running: {
      icon: Clock,
      iconColor: "white",
      iconBg: "gray.900",
      headerBg: "white",
      borderColor: "gray.300",
    },
    error: {
      icon: AlertCircle,
      iconColor: "gray.700",
      iconBg: "gray.100",
      headerBg: "gray.50",
      borderColor: "gray.300",
    },
    pending: {
      icon: Circle,
      iconColor: "gray.600",
      iconBg: "gray.100",
      headerBg: "white",
      borderColor: "gray.200",
    },
  };

  const config = statusConfig[stage.status];

  return (
    <Box position="relative">
      <Card.Root
        variant="outline"
        borderColor={config.borderColor}
        borderWidth="1px"
        overflow="hidden"
        boxShadow="none"
      >
        {/* Stage Header */}
        <Box
          as="button"
          onClick={() => setIsExpanded(!isExpanded)}
          w="full"
          bg={config.headerBg}
          px={4}
          py={3}
          textAlign="left"
          transition="all 0.15s ease"
          _hover={{ bg: "gray.50" }}
          display="flex"
          alignItems="center"
          justifyContent="space-between"
        >
          <HStack gap={3}>
            <IconContainer
              icon={config.icon}
              iconColor={config.iconColor}
              iconBg={config.iconBg}
              size="md"
            />
            <Box>
              <Text fontSize="sm" fontWeight="medium" color="gray.900">
                {stage.stage_name}
              </Text>
              {stage.execution_time && (
                <Text fontSize="xs" color="gray.500" mt={0.5}>
                  {stage.execution_time.toFixed(1)}s
                </Text>
              )}
            </Box>
          </HStack>
          <Box
            style={{
              transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
              transition: "all 0.15s ease",
            }}
          >
            <Icon as={ChevronRight} boxSize={4} color="gray.400" />
          </Box>
        </Box>

        {/* Stage Content */}
        <Collapsible.Root open={isExpanded}>
          <Collapsible.Content asChild>
            <Box
              borderTopWidth="1px"
              borderColor="gray.100"
              bg="gray.50"
              bgGradient="linear(to-b, gray.50, white)"
              p={4}
            >
              <VStack gap={4} align="stretch">
                {/* Empty state */}
                {!stage.prompt &&
                  !stage.model_output &&
                  !stage.reasoning &&
                  !stage.confidence &&
                  !stage.json_data &&
                  !stage.error && (
                    <Box
                      borderRadius="lg"
                      borderWidth="1px"
                      borderStyle="dashed"
                      borderColor="gray.200"
                      bg="white"
                      px={6}
                      py={8}
                      textAlign="center"
                    >
                      <IconContainer
                        icon={config.icon}
                        iconColor={config.iconColor}
                        iconBg={config.iconBg}
                        size="lg"
                        mx="auto"
                        mb={3}
                        opacity={0.4}
                      />
                      <Text fontSize="sm" fontWeight="medium" color="gray.600">
                        {stage.status === "completed"
                          ? "No detailed information available"
                          : stage.status === "running"
                            ? "Processing..."
                            : "Waiting to start"}
                      </Text>
                      <Text fontSize="xs" color="gray.400" mt={1}>
                        {stage.status === "completed"
                          ? "Processed before logging enabled"
                          : stage.status === "running"
                            ? "Details will appear shortly"
                            : "Pending previous stages"}
                      </Text>
                    </Box>
                  )}

                {/* Model Output */}
                {stage.model_output && (
                  <Section
                    title="AI Response"
                    description="Complete structured output from the model"
                    isExpanded={expandedSections.has("output")}
                    onToggle={() => toggleSection("output")}
                  >
                    <Box
                      borderRadius="lg"
                      borderWidth="1px"
                      borderColor="gray.200"
                      bg="white"
                      p={4}
                    >
                      <Text
                        as="pre"
                        whiteSpace="pre-wrap"
                        wordBreak="break-word"
                        fontFamily="mono"
                        fontSize="xs"
                        lineHeight="relaxed"
                        color="gray.700"
                      >
                        {typeof stage.model_output === "object"
                          ? JSON.stringify(stage.model_output, null, 2)
                          : stage.model_output}
                      </Text>
                    </Box>
                  </Section>
                )}

                {/* Constituent Drawings for Classification (Mixed Plans) */}
                {stage.stage === "classification" &&
                  stage.json_data?.constituent_drawings &&
                  Array.isArray(stage.json_data.constituent_drawings) &&
                  stage.json_data.constituent_drawings.length > 0 && (
                    <Section
                      title="Constituent Drawings Identified"
                      description={`${stage.json_data.constituent_drawings.length} drawings identified in this mixed plan document`}
                      isExpanded={expandedSections.has(
                        "constituent_drawings_classification",
                      )}
                      onToggle={() =>
                        toggleSection("constituent_drawings_classification")
                      }
                    >
                      <VStack gap={2} align="stretch">
                        {stage.json_data.constituent_drawings.map(
                          (drawing: any, idx: number) => (
                            <Box
                              key={idx}
                              borderRadius="lg"
                              borderWidth="1px"
                              borderColor="gray.200"
                              bg="white"
                              p={3}
                            >
                              <HStack gap={3} align="flex-start">
                                <Flex
                                  flexShrink={0}
                                  w={6}
                                  h={6}
                                  borderRadius="full"
                                  bg="gray.100"
                                  align="center"
                                  justify="center"
                                  fontSize="xs"
                                  fontWeight="semibold"
                                  color="gray.600"
                                >
                                  {idx + 1}
                                </Flex>
                                <Box flex={1} minW={0}>
                                  <Text
                                    fontSize="sm"
                                    fontWeight="medium"
                                    color="gray.900"
                                  >
                                    {drawing.drawing_type
                                      ?.replace(/_/g, " ")
                                      .replace(/\b\w/g, (l: string) =>
                                        l.toUpperCase(),
                                      )}
                                  </Text>
                                  <Text fontSize="xs" color="gray.600" mt={0.5}>
                                    {drawing.location_on_sheet}
                                  </Text>
                                  <Text fontSize="xs" color="gray.500" mt={1}>
                                    {drawing.description}
                                  </Text>
                                </Box>
                              </HStack>
                            </Box>
                          ),
                        )}
                      </VStack>
                    </Section>
                  )}

                {/* Reasoning & Confidence */}
                {(stage.reasoning || stage.confidence) && (
                  <Section
                    title="Decision Explanation"
                    description="Why the AI made this decision"
                    isExpanded={expandedSections.has("reasoning_confidence")}
                    onToggle={() => toggleSection("reasoning_confidence")}
                  >
                    <VStack gap={3} align="stretch">
                      {stage.reasoning && (
                        <Box
                          borderRadius="lg"
                          borderWidth="1px"
                          borderColor="gray.200"
                          bg="white"
                          p={4}
                        >
                          <Text
                            fontSize="xs"
                            fontWeight="medium"
                            color="gray.500"
                            mb={2}
                          >
                            Reasoning
                          </Text>
                          <Text
                            fontSize="sm"
                            lineHeight="relaxed"
                            color="gray.700"
                          >
                            {stage.reasoning}
                          </Text>
                        </Box>
                      )}
                      {stage.confidence && (
                        <Box
                          borderRadius="lg"
                          borderWidth="1px"
                          borderColor="gray.200"
                          bg="white"
                          p={4}
                        >
                          <Text
                            fontSize="xs"
                            fontWeight="medium"
                            color="gray.500"
                            mb={2}
                          >
                            Confidence Level
                          </Text>
                          <Text
                            fontSize="md"
                            fontWeight="semibold"
                            color="gray.900"
                          >
                            {stage.confidence}
                          </Text>
                        </Box>
                      )}
                    </VStack>
                  </Section>
                )}

                {/* Constituent Validations for Mixed Plans */}
                {stage.is_composite &&
                  stage.constituent_validations &&
                  stage.constituent_validations.length > 0 && (
                    <Section
                      title="Constituent Drawing Validations"
                      description={`Individual validation results for ${stage.constituent_validations.length} drawings`}
                      isExpanded={expandedSections.has(
                        "constituent_validations",
                      )}
                      onToggle={() => toggleSection("constituent_validations")}
                    >
                      <VStack gap={3} align="stretch">
                        {stage.constituent_validations.map(
                          (constituent, idx) => (
                            <ConstituentValidationCard
                              key={idx}
                              constituent={constituent}
                              index={idx}
                            />
                          ),
                        )}
                      </VStack>
                    </Section>
                  )}

                {/* JSON Data - only show for stages without structured output (not validation or classification) */}
                {stage.json_data &&
                  !stage.json_data.validation_checks &&
                  !stage.json_data.document_type && (
                    <Section
                      title="Technical Details"
                      description="Structured data and validation checks"
                      isExpanded={expandedSections.has("json")}
                      onToggle={() => toggleSection("json")}
                    >
                      <Box
                        borderRadius="lg"
                        borderWidth="1px"
                        borderColor="gray.200"
                        bg="white"
                        overflow="hidden"
                      >
                        <Box overflowX="auto" p={4}>
                          <Text
                            as="pre"
                            fontSize="xs"
                            lineHeight="relaxed"
                            color="gray.700"
                            fontFamily="mono"
                          >
                            {JSON.stringify(stage.json_data, null, 2)}
                          </Text>
                        </Box>
                      </Box>
                    </Section>
                  )}

                {/* Prompt */}
                {stage.prompt && (
                  <Section
                    title="Instructions Sent to AI"
                    description="The exact prompt given to the model"
                    isExpanded={expandedSections.has("prompt")}
                    onToggle={() => toggleSection("prompt")}
                    action={
                      expandedSections.has("prompt") && (
                        <Box
                          as="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setShowRawPrompt(!showRawPrompt);
                          }}
                          display="flex"
                          alignItems="center"
                          gap={1.5}
                          borderRadius="md"
                          px={2}
                          py={1}
                          fontSize="xs"
                          fontWeight="medium"
                          color="gray.600"
                          transition="all 0.15s ease"
                          _hover={{ bg: "white" }}
                        >
                          <Icon
                            as={showRawPrompt ? FileText : Code}
                            boxSize={3}
                          />
                          {showRawPrompt ? "Formatted" : "Raw"}
                        </Box>
                      )
                    }
                  >
                    <Box
                      borderRadius="lg"
                      borderWidth="1px"
                      borderColor="gray.200"
                      bg="white"
                      p={4}
                    >
                      {showRawPrompt ? (
                        <Text
                          as="pre"
                          whiteSpace="pre-wrap"
                          wordBreak="break-word"
                          fontFamily="mono"
                          fontSize="xs"
                          lineHeight="relaxed"
                          color="gray.700"
                        >
                          {stage.prompt}
                        </Text>
                      ) : (
                        <Box className="prose prose-sm prose-zinc" maxW="none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {stage.prompt}
                          </ReactMarkdown>
                        </Box>
                      )}
                    </Box>
                  </Section>
                )}

                {/* Error */}
                {stage.error && (
                  <Section
                    title="Error"
                    isExpanded={expandedSections.has("error")}
                    onToggle={() => toggleSection("error")}
                    variant="error"
                  >
                    <Box
                      borderRadius="lg"
                      borderWidth="1px"
                      borderColor="gray.300"
                      bg="gray.50"
                      p={4}
                    >
                      <HStack gap={3} align="flex-start">
                        <Icon
                          as={AlertCircle}
                          boxSize={4}
                          color="gray.900"
                          mt={0.5}
                        />
                        <Text
                          fontSize="sm"
                          lineHeight="relaxed"
                          color="gray.900"
                        >
                          {stage.error}
                        </Text>
                      </HStack>
                    </Box>
                  </Section>
                )}
              </VStack>
            </Box>
          </Collapsible.Content>
        </Collapsible.Root>
      </Card.Root>

      {/* Connector */}
      {!isLast && (
        <Flex justify="center" py={1.5}>
          <Separator
            orientation="vertical"
            h={3}
            w="1px"
            bg="gray.200"
            borderColor="gray.200"
          />
        </Flex>
      )}
    </Box>
  );
});

// Icon Container Component
interface IconContainerProps {
  icon: React.ElementType;
  iconColor: string;
  iconBg: string;
  size: "sm" | "md" | "lg";
  mx?: string;
  mb?: number;
  opacity?: number;
}

const IconContainer = memo(function IconContainer({
  icon,
  iconColor,
  iconBg,
  size,
  mx,
  mb,
  opacity,
}: IconContainerProps) {
  const sizes = {
    sm: { container: 6, icon: 3 },
    md: { container: 8, icon: 4 },
    lg: { container: 10, icon: 5 },
  };

  return (
    <Flex
      align="center"
      justify="center"
      borderRadius="lg"
      bg={iconBg}
      w={sizes[size].container}
      h={sizes[size].container}
      flexShrink={0}
      mx={mx}
      mb={mb}
      opacity={opacity}
    >
      <Icon as={icon} boxSize={sizes[size].icon} color={iconColor} />
    </Flex>
  );
});

// Section Component for consistency
interface SectionProps {
  title: string;
  description?: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  action?: React.ReactNode;
  variant?: "default" | "error";
}

const Section = memo(function Section({
  title,
  description,
  isExpanded,
  onToggle,
  children,
  action,
  variant = "default",
}: SectionProps) {
  return (
    <Box>
      <Box
        as="button"
        onClick={onToggle}
        mb={2}
        display="flex"
        w="full"
        alignItems="center"
        justifyContent="space-between"
        textAlign="left"
      >
        <VStack align="flex-start" gap={0.5}>
          <HStack gap={2}>
            <Box
              style={{
                transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
                transition: "all 0.15s ease",
              }}
            >
              <Icon as={ChevronRight} boxSize={3} />
            </Box>
            <Text
              fontSize="xs"
              fontWeight="medium"
              textTransform="uppercase"
              letterSpacing="wider"
              color={variant === "error" ? "gray.900" : "gray.500"}
            >
              {title}
            </Text>
          </HStack>
          {description && (
            <Text
              ml={5}
              fontSize="xs"
              color="gray.400"
              textTransform="none"
              letterSpacing="normal"
            >
              {description}
            </Text>
          )}
        </VStack>
        {action}
      </Box>
      <Collapsible.Root open={isExpanded}>
        <Collapsible.Content asChild>
          <Box>{children}</Box>
        </Collapsible.Content>
      </Collapsible.Root>
    </Box>
  );
});

// Constituent Validation Card Component
interface ConstituentValidationCardProps {
  constituent: ConstituentValidation;
  index: number;
}

const ConstituentValidationCard = memo(function ConstituentValidationCard({
  constituent,
  index,
}: ConstituentValidationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isValid = constituent.validation.validity_assessment === "VALID";

  return (
    <Box
      borderRadius="lg"
      borderWidth="1px"
      borderColor="gray.200"
      bg="white"
      overflow="hidden"
    >
      {/* Header */}
      <Box
        as="button"
        onClick={() => setIsExpanded(!isExpanded)}
        display="flex"
        w="full"
        alignItems="center"
        justifyContent="space-between"
        px={4}
        py={3}
        textAlign="left"
        transition="all 0.15s ease"
        _hover={{ bg: "gray.50" }}
      >
        <HStack gap={3} flex={1} minW={0}>
          <IconContainer
            icon={isValid ? CheckCircle2 : XCircle}
            iconColor={isValid ? "gray.600" : "gray.700"}
            iconBg={isValid ? "gray.100" : "gray.100"}
            size="sm"
          />
          <Box flex={1} minW={0}>
            <HStack gap={2} align="center">
              <Text fontSize="sm" fontWeight="medium" color="gray.900">
                {constituent.drawing_type
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())}
              </Text>
              <Badge
                colorPalette={isValid ? "green" : "red"}
                variant={isValid ? "subtle" : "subtle"}
                borderRadius="md"
                px={2}
                py={0.5}
                fontSize="xs"
                fontWeight="medium"
                bg={isValid ? "green.50" : "red.50"}
                color={isValid ? "green.700" : "red.700"}
              >
                {constituent.validation.validity_assessment}
              </Badge>
            </HStack>
            <Text fontSize="xs" color="gray.500" mt={0.5}>
              {constituent.location}
            </Text>
          </Box>
        </HStack>
        <Box
          style={{
            transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
            transition: "all 0.15s ease",
          }}
          flexShrink={0}
        >
          <Icon as={ChevronRight} boxSize={4} color="gray.400" />
        </Box>
      </Box>

      {/* Expanded Details */}
      <Collapsible.Root open={isExpanded}>
        <Collapsible.Content asChild>
          <Box
            borderTopWidth="1px"
            borderColor="gray.100"
            bg="gray.50"
            bgGradient="linear(to-b, gray.50, white)"
            p={4}
          >
            <VStack gap={3} align="stretch">
              {/* Description */}
              <Box
                borderRadius="lg"
                borderWidth="1px"
                borderColor="gray.200"
                bg="white"
                p={3}
              >
                <Text fontSize="xs" fontWeight="medium" color="gray.500" mb={1}>
                  Description
                </Text>
                <Text fontSize="sm" color="gray.700">
                  {constituent.description}
                </Text>
              </Box>

              {/* Reasoning */}
              {constituent.validation.assessment_reasoning && (
                <Box
                  borderRadius="lg"
                  borderWidth="1px"
                  borderColor="gray.200"
                  bg="white"
                  p={3}
                >
                  <Text
                    fontSize="xs"
                    fontWeight="medium"
                    color="gray.500"
                    mb={1}
                  >
                    Assessment Reasoning
                  </Text>
                  <Text fontSize="sm" lineHeight="relaxed" color="gray.700">
                    {constituent.validation.assessment_reasoning}
                  </Text>
                </Box>
              )}

              {/* Confidence */}
              <Box
                borderRadius="lg"
                borderWidth="1px"
                borderColor="gray.200"
                bg="white"
                p={3}
              >
                <Text fontSize="xs" fontWeight="medium" color="gray.500" mb={1}>
                  Confidence
                </Text>
                <Text fontSize="sm" fontWeight="semibold" color="gray.900">
                  {constituent.validation.overall_confidence}
                </Text>
              </Box>

              {/* Validation Checks */}
              {constituent.validation.validation_checks && (
                <Box
                  borderRadius="lg"
                  borderWidth="1px"
                  borderColor="gray.200"
                  bg="white"
                  p={3}
                >
                  <Text
                    fontSize="xs"
                    fontWeight="medium"
                    color="gray.500"
                    mb={2}
                  >
                    Validation Checks
                  </Text>
                  <Box overflowX="auto">
                    <Text
                      as="pre"
                      fontSize="xs"
                      lineHeight="relaxed"
                      color="gray.700"
                      fontFamily="mono"
                    >
                      {JSON.stringify(
                        constituent.validation.validation_checks,
                        null,
                        2,
                      )}
                    </Text>
                  </Box>
                </Box>
              )}
            </VStack>
          </Box>
        </Collapsible.Content>
      </Collapsible.Root>
    </Box>
  );
});
