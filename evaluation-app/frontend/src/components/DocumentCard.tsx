import React, { memo, useState, useEffect } from "react";
import { toast } from "sonner";
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Card,
  Heading,
  NativeSelect,
  Icon,
  Collapsible,
} from "@chakra-ui/react";
import {
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  Check,
  X,
  Edit2,
  FileText,
  ShieldCheck,
  MessageSquare,
  Target,
  Scale,
} from "lucide-react";
import { StageDetails } from "./StageDetails";
import { CarbonImpactDisplay } from "./CarbonImpact";
import { DocumentEvaluation } from "../types";
import { presets, animation } from "@/lib/design-tokens";

interface DocumentCardProps {
  document: DocumentEvaluation;
  isExpanded: boolean;
  onToggle: (documentId: string) => void;
  onReload?: () => Promise<void>;
  runId?: string;
}

export const DocumentCard = memo<DocumentCardProps>(
  function DocumentCard({
    document,
    isExpanded,
    onToggle,
    onReload,
    runId,
  }: DocumentCardProps) {
    const isCompleted = document.status === "completed";
    const isRunning = document.status === "running";
    const predictedValidity = document.final_result?.predicted_validity;
    const [isEditingGroundTruth, setIsEditingGroundTruth] = useState(false);
    const [hasBeenExpanded, setHasBeenExpanded] = useState(false);

    // Use empty string to represent "no ground truth set"
    const [localGroundTruth, setLocalGroundTruth] = useState(
      document.expected_validity &&
        document.expected_validity.toUpperCase() !== "UNKNOWN"
        ? document.expected_validity
        : "",
    );

    // Track if card has ever been expanded (for lazy loading iframe)
    useEffect(() => {
      if (isExpanded && !hasBeenExpanded) {
        setHasBeenExpanded(true);
      }
    }, [isExpanded, hasBeenExpanded]);

    const getIconVariant = () => {
      if (isRunning) return "active";
      if (isCompleted && predictedValidity === "VALID") return "success";
      if (isCompleted && predictedValidity === "INVALID") return "error";
      return "default";
    };

    const getIconComponent = () => {
      if (isRunning) return Clock;
      if (isCompleted && predictedValidity === "VALID") return CheckCircle2;
      if (isCompleted && predictedValidity === "INVALID") return XCircle;
      return CheckCircle2;
    };

    const IconComponent = getIconComponent();
    const iconVariant = getIconVariant();

    // Get colours for icon container
    const iconBgColour =
      iconVariant === "active"
        ? "gray.900"
        : iconVariant === "success"
          ? "gray.100"
          : iconVariant === "error"
            ? "gray.100"
            : "gray.100";

    const iconColour =
      iconVariant === "active"
        ? "white"
        : iconVariant === "success"
          ? "gray.700"
          : iconVariant === "error"
            ? "gray.700"
            : "gray.600";

    return (
      <Card.Root
        position="relative"
        overflow="hidden"
        borderRadius="lg"
        borderWidth="1px"
        borderColor="gray.200"
        bg="white"
        boxShadow={isExpanded ? "sm" : "none"}
        _hover={{ boxShadow: isExpanded ? "sm" : "elevated" }}
        transition="all 0.15s ease"
      >
        {/* Visual accent for document cards */}
        <Box
          position="absolute"
          left={0}
          top={0}
          bottom={0}
          width="2px"
          bg="blue.400"
          opacity={0.3}
        />

        {/* Header */}
        <Button
          onClick={() => onToggle(document.document_id)}
          width="100%"
          height="auto"
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          px={4}
          py={3}
          textAlign="left"
          bg="white"
          _hover={{ bg: "gray.50" }}
          borderRadius="0"
          variant="ghost"
        >
          <Flex align="center" gap={3} minW={0} flex={1}>
            {/* Status Icon */}
            <Flex
              align="center"
              justify="center"
              w={8}
              h={8}
              bg={iconBgColour}
              color={iconColour}
              borderRadius="md"
              flexShrink={0}
              animation={isRunning ? animation.pulse : undefined}
            >
              <Icon as={IconComponent} boxSize={4} />
            </Flex>

            {/* Document Info */}
            <VStack align="start" minW={0} flex={1} gap={1}>
              <Text
                fontSize="sm"
                fontWeight="semibold"
                color="gray.900"
                lineClamp={1}
                title={document.filename}
              >
                {document.filename}
              </Text>
              <HStack gap={2} fontSize="xs" flexWrap="wrap">
                {document.final_result ? (
                  <>
                    {/* Show ground truth vs prediction comparison */}
                    {document.expected_validity &&
                    document.expected_validity.toUpperCase() !== "UNKNOWN" ? (
                      <HStack gap={1.5}>
                        {/* Ground Truth */}
                        <HStack gap={1} color="gray.500">
                          <Text {...presets.sectionLabel} fontSize="10px">
                            Expected:
                          </Text>
                          <Badge
                            fontWeight="semibold"
                            px={1.5}
                            py={0.5}
                            borderRadius="md"
                            bg={
                              document.expected_validity.toUpperCase() ===
                              "VALID"
                                ? "green.50"
                                : document.expected_validity.toUpperCase() ===
                                    "INVALID"
                                  ? "red.50"
                                  : "gray.50"
                            }
                            color={
                              document.expected_validity.toUpperCase() ===
                              "VALID"
                                ? "green.700"
                                : document.expected_validity.toUpperCase() ===
                                    "INVALID"
                                  ? "red.700"
                                  : "gray.700"
                            }
                          >
                            {document.expected_validity.toUpperCase()}
                          </Badge>
                        </HStack>

                        <Text color="gray.300">→</Text>

                        {/* Prediction with correctness indicator */}
                        <HStack gap={1}>
                          <Text {...presets.sectionLabel} fontSize="10px">
                            Predicted:
                          </Text>
                          <Badge
                            fontWeight="semibold"
                            px={1.5}
                            py={0.5}
                            borderRadius="md"
                            bg={
                              predictedValidity === "VALID"
                                ? "green.50"
                                : predictedValidity === "INVALID"
                                  ? "red.50"
                                  : predictedValidity === "ERROR"
                                    ? "gray.100"
                                    : "gray.50"
                            }
                            color={
                              predictedValidity === "VALID"
                                ? "green.700"
                                : predictedValidity === "INVALID"
                                  ? "red.700"
                                  : predictedValidity === "ERROR"
                                    ? "gray.400"
                                    : "gray.700"
                            }
                          >
                            {predictedValidity || "Processing..."}
                          </Badge>
                          {/* Correctness badge */}
                          {document.final_result.correct !== undefined && (
                            <Badge
                              fontSize="10px"
                              fontWeight="bold"
                              px={1.5}
                              py={0.5}
                              borderRadius="md"
                              bg={
                                document.final_result.correct
                                  ? "green.100"
                                  : "red.100"
                              }
                              color={
                                document.final_result.correct
                                  ? "green.700"
                                  : "red.700"
                              }
                            >
                              {document.final_result.correct
                                ? "✓ CORRECT"
                                : "✗ WRONG"}
                            </Badge>
                          )}
                        </HStack>
                      </HStack>
                    ) : (
                      /* No ground truth - just show prediction */
                      <HStack gap={1.5}>
                        <Text {...presets.sectionLabel} fontSize="10px">
                          Predicted:
                        </Text>
                        <Badge
                          fontWeight="semibold"
                          px={1.5}
                          py={0.5}
                          borderRadius="md"
                          bg={
                            predictedValidity === "VALID"
                              ? "green.50"
                              : predictedValidity === "INVALID"
                                ? "red.50"
                                : predictedValidity === "ERROR"
                                  ? "gray.100"
                                  : "gray.50"
                          }
                          color={
                            predictedValidity === "VALID"
                              ? "green.700"
                              : predictedValidity === "INVALID"
                                ? "red.700"
                                : predictedValidity === "ERROR"
                                  ? "gray.400"
                                  : "gray.700"
                          }
                        >
                          {predictedValidity || "Processing..."}
                        </Badge>
                        <Text
                          fontSize="10px"
                          color="gray.400"
                          fontStyle="italic"
                        >
                          (no ground truth)
                        </Text>
                      </HStack>
                    )}

                    {document.final_result.execution_time && (
                      <>
                        <Text color="gray.300">·</Text>
                        <Text color="gray.500">
                          {document.final_result.execution_time.toFixed(1)}s
                        </Text>
                      </>
                    )}
                  </>
                ) : (
                  <Text color="gray.400">Pending...</Text>
                )}
              </HStack>
            </VStack>

            {/* Stage Progress */}
            <HStack gap={1} flexShrink={0}>
              {document.stages.map((stage) => (
                <Box
                  key={stage.stage}
                  title={stage.stage_name}
                  h={1.5}
                  w={1.5}
                  borderRadius="full"
                  transition="all 0.15s ease"
                  bg={
                    stage.status === "completed"
                      ? "gray.400"
                      : stage.status === "running"
                        ? "gray.900"
                        : stage.status === "error"
                          ? "gray.900"
                          : "gray.200"
                  }
                  animation={
                    stage.status === "running" ? animation.pulse : undefined
                  }
                />
              ))}
            </HStack>

            {/* Chevron */}
            <Icon
              as={ChevronRight}
              boxSize={4}
              flexShrink={0}
              color="gray.400"
              transition="transform 0.15s ease"
              transform={isExpanded ? "rotate(90deg)" : "rotate(0)"}
            />
          </Flex>
        </Button>

        {/* Expanded Content */}
        <Collapsible.Root open={isExpanded}>
          <Collapsible.Content asChild>
            <Box borderTop="1px" borderColor="gray.100" bg="gray.50/30" p={4}>
              <Box
                display="grid"
                gridTemplateColumns={{ base: "1fr", lg: "1fr 1fr" }}
                gap={4}
              >
                {/* Left Column - Document Preview */}
                <VStack gap={4} align="stretch">
                  {/* Document Viewer */}
                  <Card.Root
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor="gray.200"
                    bg="white"
                    overflow="hidden"
                  >
                    <Card.Header
                      bg="gray.50"
                      borderBottom="1px"
                      borderColor="gray.200"
                      px={4}
                      py={2}
                    >
                      <Heading size="xs" {...presets.sectionLabel}>
                        Document Preview
                      </Heading>
                    </Card.Header>
                    <Card.Body p={0}>
                      <Box position="relative" bg="gray.100" h="500px">
                        {hasBeenExpanded ? (
                          <iframe
                            src={`http://localhost:8000/api/documents/${encodeURIComponent(document.filename)}/file#view=FitH&toolbar=0&navpanes=0&scrollbar=0`}
                            title={`Preview of ${document.filename}`}
                            style={{
                              position: "absolute",
                              inset: 0,
                              width: "100%",
                              height: "100%",
                              border: "none",
                              opacity: isExpanded ? 1 : 0,
                              transition: "opacity 0.15s ease",
                            }}
                          />
                        ) : (
                          <Flex
                            position="absolute"
                            inset={0}
                            align="center"
                            justify="center"
                            color="gray.400"
                            fontSize="sm"
                          >
                            Expand to load document preview
                          </Flex>
                        )}
                      </Box>
                    </Card.Body>
                  </Card.Root>

                  {/* Ground Truth vs Prediction Comparison */}
                  {document.final_result && (
                    <Card.Root
                      borderRadius="lg"
                      borderWidth="1px"
                      borderColor="gray.200"
                      bg="white"
                    >
                      <Card.Header
                        bg="orange.50/50"
                        borderBottom="1px"
                        borderColor="orange.100"
                        px={4}
                        py={2}
                      >
                        <Flex align="center" justify="space-between">
                          <HStack gap={2}>
                            <Icon as={Target} boxSize={4} color="orange.600" />
                            <Heading
                              size="xs"
                              {...presets.sectionLabel}
                              color="orange.700"
                            >
                              Ground Truth Comparison
                            </Heading>
                          </HStack>
                          {!isEditingGroundTruth &&
                            localGroundTruth.toUpperCase() !== "UNKNOWN" && (
                              <Button
                                onClick={() => setIsEditingGroundTruth(true)}
                                size="xs"
                                color="gray.500"
                                _hover={{ color: "gray.900", bg: "gray.100" }}
                                variant="ghost"
                                fontWeight="medium"
                              >
                                <Icon as={Edit2} boxSize={3} mr={1.5} />
                                Edit
                              </Button>
                            )}
                        </Flex>
                      </Card.Header>
                      <Card.Body p={4}>
                        <VStack gap={3} align="stretch" fontSize="xs">
                          {/* Expected (Ground Truth) */}
                          <Flex justify="space-between" align="baseline">
                            <Text color="gray.600" fontWeight="medium">
                              Expected Validity
                            </Text>
                            {isEditingGroundTruth ? (
                              <VStack flex={1} ml={4} gap={2} align="stretch">
                                <NativeSelect.Root size="xs">
                                  <NativeSelect.Field
                                    value={localGroundTruth}
                                    onChange={(e) =>
                                      setLocalGroundTruth(e.target.value)
                                    }
                                  >
                                    <option value="">-- No label --</option>
                                    <option value="VALID">VALID</option>
                                    <option value="INVALID">INVALID</option>
                                    <option value="CLARIFICATION_NEEDED">
                                      CLARIFICATION_NEEDED
                                    </option>
                                  </NativeSelect.Field>
                                </NativeSelect.Root>
                                <HStack gap={2}>
                                  <Button
                                    onClick={async () => {
                                      // Validate that a label is selected
                                      if (!localGroundTruth) {
                                        toast.error(
                                          "Please select a validity label (VALID, INVALID, or CLARIFICATION_NEEDED)",
                                        );
                                        return;
                                      }

                                      try {
                                        const response = await fetch(
                                          "/api/update-document-ground-truth",
                                          {
                                            method: "POST",
                                            headers: {
                                              "Content-Type":
                                                "application/json",
                                            },
                                            body: JSON.stringify({
                                              document_id: document.document_id,
                                              expected_validity:
                                                localGroundTruth,
                                              run_id: runId,
                                            }),
                                          },
                                        );

                                        if (response.ok) {
                                          setIsEditingGroundTruth(false);
                                          // Reload the run to show updated ground truth and correctness
                                          if (onReload) {
                                            await onReload();
                                          }
                                        } else {
                                          const errorData =
                                            await response.json();
                                          toast.error(
                                            `Failed to save ground truth: ${errorData.detail || "Unknown error"}`,
                                          );
                                        }
                                      } catch (error) {
                                        console.error(
                                          "Failed to save ground truth:",
                                          error,
                                        );
                                        toast.error(
                                          "Failed to save ground truth. Check console for details.",
                                        );
                                      }
                                    }}
                                    flex={1}
                                    size="xs"
                                    bg="gray.900"
                                    color="white"
                                    fontWeight="medium"
                                    _hover={{ bg: "gray.800" }}
                                  >
                                    Save
                                  </Button>
                                  <Button
                                    onClick={() => {
                                      setLocalGroundTruth(
                                        document.expected_validity &&
                                          document.expected_validity.toUpperCase() !==
                                            "UNKNOWN"
                                          ? document.expected_validity
                                          : "",
                                      );
                                      setIsEditingGroundTruth(false);
                                    }}
                                    flex={1}
                                    size="xs"
                                    variant="ghost"
                                    color="gray.700"
                                    fontWeight="medium"
                                    _hover={{ bg: "gray.100" }}
                                  >
                                    Cancel
                                  </Button>
                                </HStack>
                              </VStack>
                            ) : localGroundTruth.toUpperCase() !== "UNKNOWN" ? (
                              <Badge
                                fontWeight="semibold"
                                px={2}
                                py={0.5}
                                borderRadius="md"
                                bg={
                                  localGroundTruth.toUpperCase() === "VALID"
                                    ? "green.100"
                                    : localGroundTruth.toUpperCase() ===
                                        "INVALID"
                                      ? "red.100"
                                      : localGroundTruth.toUpperCase() ===
                                          "CLARIFICATION_NEEDED"
                                        ? "orange.100"
                                        : "gray.100"
                                }
                                color={
                                  localGroundTruth.toUpperCase() === "VALID"
                                    ? "green.800"
                                    : localGroundTruth.toUpperCase() ===
                                        "INVALID"
                                      ? "red.800"
                                      : localGroundTruth.toUpperCase() ===
                                          "CLARIFICATION_NEEDED"
                                        ? "orange.800"
                                        : "gray.800"
                                }
                              >
                                {localGroundTruth.toUpperCase()}
                              </Badge>
                            ) : (
                              <Button
                                onClick={() => setIsEditingGroundTruth(true)}
                                size="xs"
                                color="gray.500"
                                _hover={{ color: "gray.900", bg: "gray.100" }}
                                variant="ghost"
                                fontWeight="medium"
                              >
                                <Icon as={Edit2} boxSize={3} mr={1.5} />
                                Add label
                              </Button>
                            )}
                          </Flex>

                          {/* Predicted */}
                          <Flex
                            justify="space-between"
                            align="baseline"
                            pt={2}
                            borderTop="1px"
                            borderColor="gray.100"
                          >
                            <Text color="gray.600" fontWeight="medium">
                              Model Prediction
                            </Text>
                            <Badge
                              fontWeight="semibold"
                              px={2}
                              py={0.5}
                              borderRadius="md"
                              bg={
                                predictedValidity === "VALID"
                                  ? "green.100"
                                  : predictedValidity === "INVALID"
                                    ? "red.100"
                                    : predictedValidity === "ERROR"
                                      ? "gray.100"
                                      : "gray.50"
                              }
                              color={
                                predictedValidity === "VALID"
                                  ? "green.800"
                                  : predictedValidity === "INVALID"
                                    ? "red.800"
                                    : predictedValidity === "ERROR"
                                      ? "gray.400"
                                      : "gray.700"
                              }
                            >
                              {predictedValidity || "Processing..."}
                            </Badge>
                          </Flex>

                          {/* Correctness Status */}
                          {localGroundTruth &&
                            localGroundTruth.toUpperCase() !== "UNKNOWN" &&
                            document.final_result.correct !== undefined && (
                              <Flex
                                justify="space-between"
                                align="baseline"
                                pt={2}
                                borderTop="1px"
                                borderColor="gray.100"
                              >
                                <Text color="gray.600" fontWeight="medium">
                                  Assessment
                                </Text>
                                <HStack
                                  fontWeight="semibold"
                                  color={
                                    document.final_result.correct
                                      ? "green.700"
                                      : "red.700"
                                  }
                                >
                                  {document.final_result.correct ? (
                                    <>
                                      <Icon as={Check} boxSize={3} />
                                      <Text>Correct</Text>
                                    </>
                                  ) : (
                                    <>
                                      <Icon as={X} boxSize={3} />
                                      <Text>Incorrect</Text>
                                    </>
                                  )}
                                </HStack>
                              </Flex>
                            )}
                        </VStack>
                        <Text
                          mt={3}
                          pt={3}
                          borderTop="1px"
                          borderColor="gray.100"
                          fontSize="10px"
                          color="gray.500"
                          lineHeight="relaxed"
                        >
                          Compare model predictions against expected validity
                          labels for accuracy assessment.
                        </Text>
                      </Card.Body>
                    </Card.Root>
                  )}

                  {/* Classification Summary Card */}
                  {document.final_result &&
                    (() => {
                      const classificationStage = document.stages.find(
                        (s) => s.stage === "classification",
                      );
                      if (classificationStage?.json_data?.document_type) {
                        return (
                          <Card.Root
                            borderRadius="lg"
                            borderWidth="1px"
                            borderColor="gray.200"
                            bg="white"
                          >
                            <Card.Header
                              bg="blue.50/50"
                              borderBottom="1px"
                              borderColor="blue.100"
                              px={4}
                              py={2}
                            >
                              <HStack gap={2}>
                                <Icon
                                  as={FileText}
                                  boxSize={4}
                                  color="blue.600"
                                />
                                <Heading
                                  size="xs"
                                  {...presets.sectionLabel}
                                  color="blue.700"
                                >
                                  Classification
                                </Heading>
                              </HStack>
                            </Card.Header>
                            <Card.Body p={4}>
                              <VStack gap={3} align="stretch" fontSize="xs">
                                <Flex justify="space-between" align="baseline">
                                  <Text color="gray.600" fontWeight="medium">
                                    Document Type
                                  </Text>
                                  <Text color="gray.900" fontWeight="semibold">
                                    {String(
                                      classificationStage.json_data
                                        .document_type,
                                    )
                                      .replace(/_/g, " ")
                                      .replace(/\b\w/g, (l: string) =>
                                        l.toUpperCase(),
                                      )}
                                  </Text>
                                </Flex>
                                {classificationStage.confidence && (
                                  <Flex
                                    justify="space-between"
                                    align="baseline"
                                    pt={2}
                                    borderTop="1px"
                                    borderColor="gray.100"
                                  >
                                    <Text color="gray.600" fontWeight="medium">
                                      Confidence
                                    </Text>
                                    <Text color="gray.900" fontFamily="mono">
                                      {classificationStage.confidence}
                                    </Text>
                                  </Flex>
                                )}
                              </VStack>
                              <Text
                                mt={3}
                                pt={3}
                                borderTop="1px"
                                borderColor="gray.100"
                                fontSize="10px"
                                color="gray.500"
                                lineHeight="relaxed"
                              >
                                Automatic document type classification for
                                appropriate validation rules.
                              </Text>
                            </Card.Body>
                          </Card.Root>
                        );
                      }
                      return null;
                    })()}

                  {/* Validation Summary Card */}
                  {document.final_result &&
                    (() => {
                      const validationStage = document.stages.find(
                        (s) => s.stage === "validation",
                      );
                      if (validationStage?.json_data?.validity_assessment) {
                        const validity = String(
                          validationStage.json_data.validity_assessment,
                        );
                        const isValid = validity === "VALID";

                        return (
                          <Card.Root
                            borderRadius="lg"
                            borderWidth="1px"
                            borderColor="gray.200"
                            bg="white"
                          >
                            <Card.Header
                              bg={isValid ? "green.50/50" : "red.50/50"}
                              borderBottom="1px"
                              borderColor={isValid ? "green.100" : "red.100"}
                              px={4}
                              py={2}
                            >
                              <HStack gap={2}>
                                <Icon
                                  as={ShieldCheck}
                                  boxSize={4}
                                  color={isValid ? "green.600" : "red.600"}
                                />
                                <Heading
                                  size="xs"
                                  {...presets.sectionLabel}
                                  color={isValid ? "green.700" : "red.700"}
                                >
                                  Validation Assessment
                                </Heading>
                              </HStack>
                            </Card.Header>
                            <Card.Body p={4}>
                              <VStack gap={3} align="stretch" fontSize="xs">
                                <Flex justify="space-between" align="baseline">
                                  <Text color="gray.600" fontWeight="medium">
                                    Status
                                  </Text>
                                  <Badge
                                    fontWeight="semibold"
                                    px={2}
                                    py={0.5}
                                    borderRadius="md"
                                    bg={isValid ? "green.100" : "red.100"}
                                    color={isValid ? "green.800" : "red.800"}
                                  >
                                    {validity}
                                  </Badge>
                                </Flex>
                                {validationStage.confidence && (
                                  <Flex
                                    justify="space-between"
                                    align="baseline"
                                    pt={2}
                                    borderTop="1px"
                                    borderColor="gray.100"
                                  >
                                    <Text color="gray.600" fontWeight="medium">
                                      Confidence
                                    </Text>
                                    <Text color="gray.900" fontFamily="mono">
                                      {validationStage.confidence}
                                    </Text>
                                  </Flex>
                                )}
                              </VStack>
                              <Text
                                mt={3}
                                pt={3}
                                borderTop="1px"
                                borderColor="gray.100"
                                fontSize="10px"
                                color="gray.500"
                                lineHeight="relaxed"
                              >
                                Comprehensive validation against planning
                                requirements and regulations.
                              </Text>
                            </Card.Body>
                          </Card.Root>
                        );
                      }
                      return null;
                    })()}

                  {/* Final Reasoning Card */}
                  {document.final_result && (
                    <Card.Root
                      borderRadius="lg"
                      borderWidth="1px"
                      borderColor="gray.200"
                      bg="white"
                    >
                      <Card.Header
                        bg="purple.50/50"
                        borderBottom="1px"
                        borderColor="purple.100"
                        px={4}
                        py={2}
                      >
                        <HStack gap={2}>
                          <Icon
                            as={MessageSquare}
                            boxSize={4}
                            color="purple.600"
                          />
                          <Heading
                            size="xs"
                            {...presets.sectionLabel}
                            color="purple.700"
                          >
                            Final Reasoning
                          </Heading>
                        </HStack>
                      </Card.Header>
                      <Card.Body p={4}>
                        <Text
                          fontSize="sm"
                          lineHeight="relaxed"
                          color="gray.700"
                          mb={3}
                        >
                          {document.final_result.predicted_reasoning}
                        </Text>
                        <Box
                          display="grid"
                          gridTemplateColumns="repeat(2, 1fr)"
                          gap={3}
                          pt={3}
                          borderTop="1px"
                          borderColor="gray.100"
                          fontSize="xs"
                        >
                          <VStack align="start" gap={1}>
                            <Text color="gray.600" fontWeight="medium">
                              Confidence
                            </Text>
                            <Text color="gray.900" fontFamily="mono">
                              {document.final_result.confidence}
                            </Text>
                          </VStack>
                          {document.final_result.prompt_type && (
                            <VStack align="start" gap={1}>
                              <Text color="gray.600" fontWeight="medium">
                                Prompt Type
                              </Text>
                              <Text color="gray.900" fontFamily="mono">
                                {document.final_result.prompt_type}
                              </Text>
                            </VStack>
                          )}
                        </Box>
                        <Text
                          mt={3}
                          pt={3}
                          borderTop="1px"
                          borderColor="gray.100"
                          fontSize="10px"
                          color="gray.500"
                          lineHeight="relaxed"
                        >
                          Model's detailed explanation of the validity
                          assessment and decision rationale.
                        </Text>
                      </Card.Body>
                    </Card.Root>
                  )}

                  {/* Reasoning Evaluation Card */}
                  {document.final_result?.reasoning_evaluated && (
                    <Card.Root
                      borderRadius="lg"
                      borderWidth="1px"
                      borderColor="gray.200"
                      bg="white"
                    >
                      <Card.Header
                        bg="cyan.50/50"
                        borderBottom="1px"
                        borderColor="cyan.100"
                        px={4}
                        py={2}
                      >
                        <Flex align="center" justify="space-between">
                          <HStack gap={2}>
                            <Icon as={Scale} boxSize={4} color="cyan.600" />
                            <Heading
                              size="xs"
                              {...presets.sectionLabel}
                              color="cyan.700"
                            >
                              Reasoning Evaluation
                            </Heading>
                          </HStack>
                          {document.final_result.reasoning_match_score !=
                            null && (
                            <Badge
                              fontWeight="semibold"
                              px={2}
                              py={0.5}
                              borderRadius="md"
                              bg={
                                document.final_result.reasoning_match_score >=
                                0.8
                                  ? "green.100"
                                  : document.final_result
                                        .reasoning_match_score >= 0.5
                                    ? "yellow.100"
                                    : "red.100"
                              }
                              color={
                                document.final_result.reasoning_match_score >=
                                0.8
                                  ? "green.800"
                                  : document.final_result
                                        .reasoning_match_score >= 0.5
                                    ? "yellow.800"
                                    : "red.800"
                              }
                            >
                              {(
                                document.final_result.reasoning_match_score *
                                100
                              ).toFixed(0)}
                              % Match
                            </Badge>
                          )}
                        </Flex>
                      </Card.Header>
                      <Card.Body p={4}>
                        <VStack gap={4} align="stretch">
                          {/* Match Score Visual */}
                          {document.final_result.reasoning_match_score !=
                            null && (
                            <Box>
                              <Flex justify="space-between" mb={1}>
                                <Text
                                  fontSize="xs"
                                  color="gray.600"
                                  fontWeight="medium"
                                >
                                  Semantic Match Score
                                </Text>
                                <Text
                                  fontSize="xs"
                                  color="gray.900"
                                  fontFamily="mono"
                                >
                                  {(
                                    document.final_result
                                      .reasoning_match_score * 100
                                  ).toFixed(1)}
                                  %
                                </Text>
                              </Flex>
                              <Box
                                h={2}
                                bg="gray.100"
                                borderRadius="full"
                                overflow="hidden"
                              >
                                <Box
                                  h="100%"
                                  w={`${document.final_result.reasoning_match_score * 100}%`}
                                  bg={
                                    document.final_result
                                      .reasoning_match_score >= 0.8
                                      ? "green.500"
                                      : document.final_result
                                            .reasoning_match_score >= 0.5
                                        ? "yellow.500"
                                        : "red.500"
                                  }
                                  borderRadius="full"
                                  transition="width 0.25s ease"
                                />
                              </Box>
                            </Box>
                          )}

                          {/* Judge Explanation */}
                          {document.final_result.reasoning_explanation && (
                            <Box pt={3} borderTop="1px" borderColor="gray.100">
                              <Text
                                fontSize="xs"
                                color="gray.600"
                                fontWeight="medium"
                                mb={2}
                              >
                                Evaluation Summary
                              </Text>
                              <Text
                                fontSize="sm"
                                lineHeight="relaxed"
                                color="gray.700"
                                bg="gray.50"
                                p={3}
                                borderRadius="md"
                              >
                                {document.final_result.reasoning_explanation}
                              </Text>
                            </Box>
                          )}
                        </VStack>
                        <Text
                          mt={3}
                          pt={3}
                          borderTop="1px"
                          borderColor="gray.100"
                          fontSize="10px"
                          color="gray.500"
                          lineHeight="relaxed"
                        >
                          LLM-as-judge evaluation comparing model reasoning
                          against expected ground truth reasoning.
                        </Text>
                      </Card.Body>
                    </Card.Root>
                  )}

                  {/* Carbon Impact Display */}
                  {document.final_result?.carbon_impact && (
                    <CarbonImpactDisplay
                      impact={document.final_result.carbon_impact}
                    />
                  )}
                </VStack>

                {/* Right Column - Stages */}
                <Box>
                  <Heading size="xs" {...presets.sectionLabel} mb={3}>
                    Evaluation Stages
                  </Heading>
                  <StageDetails stages={document.stages} />
                </Box>
              </Box>
            </Box>
          </Collapsible.Content>
        </Collapsible.Root>
      </Card.Root>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison: only re-render if document data or state actually changed
    const doc1 = prevProps.document;
    const doc2 = nextProps.document;

    // If it's a different document, always re-render
    if (doc1.document_id !== doc2.document_id) {
      return false;
    }

    // Check if status changed
    if (doc1.status !== doc2.status) {
      return false;
    }

    // Check if expansion state changed
    if (prevProps.isExpanded !== nextProps.isExpanded) {
      return false;
    }

    // Check if final result changed
    const result1 = doc1.final_result;
    const result2 = doc2.final_result;
    if (result1 !== result2) {
      if (!result1 || !result2) return false;
      if (
        result1.predicted_validity !== result2.predicted_validity ||
        result1.confidence !== result2.confidence ||
        result1.execution_time !== result2.execution_time ||
        result1.reasoning_evaluated !== result2.reasoning_evaluated ||
        result1.reasoning_match_score !== result2.reasoning_match_score ||
        result1.reasoning_explanation !== result2.reasoning_explanation
      ) {
        return false;
      }
    }

    // Check if stages changed
    if (doc1.stages.length !== doc2.stages.length) {
      return false;
    }
    for (let i = 0; i < doc1.stages.length; i++) {
      const stage1 = doc1.stages[i];
      const stage2 = doc2.stages[i];
      if (
        stage1.status !== stage2.status ||
        stage1.reasoning !== stage2.reasoning ||
        stage1.execution_time !== stage2.execution_time
      ) {
        return false;
      }
    }

    // Check if runId changed (callbacks should be stable from useCallback)
    if (prevProps.runId !== nextProps.runId) {
      return false;
    }

    // All checks passed, props are equal, skip re-render
    return true;
  },
);
