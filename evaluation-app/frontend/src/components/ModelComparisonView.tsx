import React, { useState, useEffect, useMemo } from "react";
import {
  Box,
  Card,
  Flex,
  VStack,
  HStack,
  Text,
  Badge,
  Button,
  Icon,
  Spinner,
  Collapsible,
  IconButton,
  Switch,
} from "@chakra-ui/react";
import {
  BarChart3,
  FileText,
  ChevronDown,
  ChevronUp,
  Cpu,
  Info,
  Brain,
} from "lucide-react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { ModelStats } from "@/types";
import { animation, presets } from "@/lib/design-tokens";
import { SimpleTooltip } from "@/lib/chakra-compat";

// Metric explanations for binary classification
const METRIC_EXPLANATIONS = {
  accuracy:
    "Accuracy measures the proportion of all predictions that were correct. Formula: (TP + TN) / Total",
  precision:
    "Precision measures how many predicted positives (VALID) were actually correct. High precision = few false alarms. Formula: TP / (TP + FP)",
  recall:
    "Recall measures how many actual positives (VALID) were correctly identified. High recall = few missed cases. Formula: TP / (TP + FN)",
  f1Score:
    "F1 Score is the harmonic mean of precision and recall, providing a balanced measure. Formula: 2 × (Precision × Recall) / (Precision + Recall)",
  reasoningAccuracy:
    "Reasoning accuracy measures how well the model's reasoning matches the expected reasoning from ground truth. Evaluated using LLM-as-judge.",
};

const MotionBox = motion.div;

type SortField =
  | "accuracy"
  | "runs"
  | "time"
  | "f1"
  | "name"
  | "reasoning"
  | "precision"
  | "recall";
type SortDirection = "asc" | "desc";

interface ModelComparisonViewProps {
  onLoadRun?: (runId: string) => void;
}

export function ModelComparisonView({ onLoadRun }: ModelComparisonViewProps) {
  const [models, setModels] = useState<ModelStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedModel, setExpandedModel] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>("accuracy");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [groupByReasoningEffort, setGroupByReasoningEffort] = useState(true);

  useEffect(() => {
    loadModelStats();
  }, [groupByReasoningEffort]);

  const loadModelStats = async () => {
    setLoading(true);
    try {
      const data = await api.runs.getStatsByModel(groupByReasoningEffort);
      setModels(data.model_stats || []);
    } catch (error) {
      console.error("Failed to load model stats:", error);
    } finally {
      setLoading(false);
    }
  };

  // Generate a unique key for each model entry (includes reasoning_effort when grouped)
  const getModelKey = (model: ModelStats) => {
    if (groupByReasoningEffort && model.reasoning_effort) {
      return `${model.model_name}|${model.reasoning_effort}`;
    }
    return model.model_name;
  };

  // Format reasoning effort for display
  const formatReasoningEffort = (effort: string | null) => {
    if (!effort) return "Default";
    return effort.charAt(0).toUpperCase() + effort.slice(1);
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const sortedModels = useMemo(() => {
    return [...models].sort((a, b) => {
      let aVal: number | string;
      let bVal: number | string;

      switch (sortField) {
        case "accuracy":
          aVal = a.avg_accuracy ?? -1;
          bVal = b.avg_accuracy ?? -1;
          break;
        case "runs":
          aVal = a.run_count;
          bVal = b.run_count;
          break;
        case "time":
          aVal = a.avg_execution_time ?? Infinity;
          bVal = b.avg_execution_time ?? Infinity;
          break;
        case "f1":
          aVal = a.avg_f1_score ?? -1;
          bVal = b.avg_f1_score ?? -1;
          break;
        case "precision":
          aVal = a.avg_precision ?? -1;
          bVal = b.avg_precision ?? -1;
          break;
        case "recall":
          aVal = a.avg_recall ?? -1;
          bVal = b.avg_recall ?? -1;
          break;
        case "reasoning":
          aVal = a.avg_reasoning_accuracy ?? -1;
          bVal = b.avg_reasoning_accuracy ?? -1;
          break;
        case "name":
          aVal = a.model_name.toLowerCase();
          bVal = b.model_name.toLowerCase();
          break;
        default:
          return 0;
      }

      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDirection === "asc"
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      return sortDirection === "asc"
        ? (aVal as number) - (bVal as number)
        : (bVal as number) - (aVal as number);
    });
  }, [models, sortField, sortDirection]);

  const getAccuracyColor = (accuracy: number | null) => {
    if (accuracy === null) return "gray.500";
    if (accuracy >= 90) return "green.500";
    if (accuracy >= 70) return "yellow.500";
    return "red.500";
  };

  if (loading) {
    return (
      <Flex align="center" justify="center" py={16}>
        <VStack gap={2}>
          <Spinner size="lg" color="gray.300" />
          <Text fontSize="sm" color="fg.muted">
            Loading model statistics...
          </Text>
        </VStack>
      </Flex>
    );
  }

  if (models.length === 0) {
    return (
      <Flex align="center" justify="center" py={16}>
        <VStack gap={2}>
          <Icon as={BarChart3} boxSize={8} color="gray.300" />
          <Text fontSize="sm" fontWeight="medium" color="fg.muted">
            No model data available
          </Text>
          <Text fontSize="xs" color="gray.400">
            Run evaluations with different models to see comparisons
          </Text>
        </VStack>
      </Flex>
    );
  }

  return (
    <VStack gap={6} align="stretch">
      {/* Header */}
      <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
        <Box>
          <Text fontSize="lg" fontWeight="semibold" color="fg.emphasis">
            Model Comparison
          </Text>
          <Text mt={0.5} fontSize="sm" color="fg.muted">
            Comparing {models.length}{" "}
            {models.length === 1 ? "configuration" : "configurations"}
          </Text>
        </Box>
        <HStack gap={2}>
          <Text fontSize="sm" color="fg.muted">
            Group by thinking effort
          </Text>
          <Switch.Root
            checked={groupByReasoningEffort}
            onCheckedChange={(e: { checked: boolean }) =>
              setGroupByReasoningEffort(e.checked)
            }
            colorPalette="purple"
          >
            <Switch.HiddenInput />
            <Switch.Control>
              <Switch.Thumb />
            </Switch.Control>
          </Switch.Root>
        </HStack>
      </Flex>

      {/* Sort Controls */}
      <Card.Root
        borderRadius="lg"
        boxShadow="none"
        borderWidth="1px"
        borderColor="gray.200"
      >
        <Card.Body p={0}>
          <Flex minH={12} align="center" px={4} gap={2} flexWrap="wrap" py={2}>
            <Text {...presets.sectionLabel} color="gray.400" mr={2}>
              Sort by
            </Text>
            {[
              { field: "accuracy" as SortField, label: "Accuracy" },
              { field: "reasoning" as SortField, label: "Reasoning" },
              { field: "f1" as SortField, label: "F1" },
              { field: "precision" as SortField, label: "Precision" },
              { field: "recall" as SortField, label: "Recall" },
              { field: "time" as SortField, label: "Time" },
              { field: "runs" as SortField, label: "Runs" },
              { field: "name" as SortField, label: "Name" },
            ].map((item) => (
              <Button
                key={item.field}
                size="sm"
                variant={sortField === item.field ? "solid" : "ghost"}
                bg={sortField === item.field ? "gray.900" : "transparent"}
                color={sortField === item.field ? "white" : "fg.muted"}
                fontWeight="medium"
                onClick={() => handleSort(item.field)}
                _hover={{
                  bg: sortField === item.field ? "gray.800" : "gray.100",
                }}
              >
                {item.label}
                {sortField === item.field && (
                  <Icon
                    as={sortDirection === "asc" ? ChevronUp : ChevronDown}
                    boxSize={3}
                    ml={1}
                  />
                )}
              </Button>
            ))}
          </Flex>
        </Card.Body>
      </Card.Root>

      {/* Model Cards */}
      <VStack gap={3} align="stretch">
        {sortedModels.map((model, index) => (
          <MotionBox
            key={getModelKey(model)}
            {...animation.slideUp}
            transition={{ duration: 0.3, delay: index * 0.05 }}
          >
            <Box
              borderRadius="lg"
              boxShadow="none"
              borderWidth="1px"
              borderColor="gray.200"
              overflow="hidden"
              position="relative"
            >
              {/* Accent bar */}
              <Box
                position="absolute"
                left={0}
                top={0}
                bottom={0}
                width="4px"
                bg={getAccuracyColor(model.avg_accuracy)}
              />

              <Box>
                {/* Main Row */}
                <Flex
                  align="center"
                  px={4}
                  py={3}
                  cursor="pointer"
                  onClick={() =>
                    setExpandedModel(
                      expandedModel === getModelKey(model)
                        ? null
                        : getModelKey(model),
                    )
                  }
                  _hover={{ bg: "gray.50" }}
                  transition="all 0.15s ease"
                >
                  {/* Model Info - fixed width for consistent metrics alignment */}
                  <Flex
                    align="center"
                    w="420px"
                    minW="420px"
                    gap={3}
                    pl={2}
                    flexShrink={0}
                  >
                    <Flex
                      align="center"
                      justify="center"
                      boxSize={10}
                      borderRadius="lg"
                      bg="purple.50"
                      flexShrink={0}
                    >
                      <Icon as={Cpu} boxSize={5} color="purple.500" />
                    </Flex>
                    <Box flex={1} minW={0}>
                      <HStack gap={2} align="center">
                        <Text
                          fontSize="sm"
                          fontWeight="semibold"
                          color={
                            sortField === "name" ? "blue.600" : "fg.emphasis"
                          }
                          lineClamp={1}
                          px={sortField === "name" ? 1.5 : 0}
                          py={sortField === "name" ? 0.5 : 0}
                          bg={sortField === "name" ? "blue.50" : "transparent"}
                        >
                          {model.model_name}
                        </Text>
                        {groupByReasoningEffort && model.reasoning_effort && (
                          <Badge colorPalette="purple" variant="subtle" px={2}>
                            <HStack gap={1}>
                              <Icon as={Brain} boxSize={3} />
                              <Text>
                                {formatReasoningEffort(model.reasoning_effort)}
                              </Text>
                            </HStack>
                          </Badge>
                        )}
                      </HStack>
                      <HStack gap={3} mt={1} fontSize="xs" color="fg.muted">
                        <Flex
                          align="center"
                          gap={1}
                          px={1.5}
                          py={0.5}
                          bg={sortField === "runs" ? "blue.50" : "transparent"}
                          borderWidth={sortField === "runs" ? "1px" : "0"}
                          borderColor="blue.200"
                        >
                          <Icon
                            as={BarChart3}
                            boxSize={3}
                            color={
                              sortField === "runs" ? "blue.500" : "inherit"
                            }
                          />
                          <Text
                            color={
                              sortField === "runs" ? "blue.600" : "inherit"
                            }
                            fontWeight={
                              sortField === "runs" ? "medium" : "normal"
                            }
                          >
                            {model.run_count}{" "}
                            {model.run_count === 1 ? "run" : "runs"}
                          </Text>
                        </Flex>
                        <Flex align="center" gap={1}>
                          <Icon as={FileText} boxSize={3} />
                          <Text>{model.total_documents} docs</Text>
                        </Flex>
                      </HStack>
                    </Box>
                  </Flex>

                  {/* Metrics */}
                  <HStack gap={3} mr={4} flexWrap="wrap" justify="flex-end">
                    {/* Accuracy */}
                    <SimpleTooltip label={METRIC_EXPLANATIONS.accuracy}>
                      <Box
                        textAlign="center"
                        minW="70px"
                        cursor="help"
                        p={1}
                        bg={
                          sortField === "accuracy" ? "blue.50" : "transparent"
                        }
                        borderWidth={sortField === "accuracy" ? "1px" : "0"}
                        borderColor="blue.200"
                      >
                        <Text
                          fontSize="xs"
                          color={
                            sortField === "accuracy" ? "blue.600" : "fg.muted"
                          }
                          mb={0.5}
                        >
                          Accuracy
                        </Text>
                        <Text
                          fontSize="sm"
                          fontWeight="semibold"
                          color={
                            model.avg_accuracy !== null
                              ? getAccuracyColor(model.avg_accuracy)
                              : "gray.400"
                          }
                        >
                          {model.avg_accuracy !== null
                            ? `${(model.avg_accuracy * 100).toFixed(1)}%`
                            : "-"}
                        </Text>
                      </Box>
                    </SimpleTooltip>

                    {/* Precision */}
                    <SimpleTooltip label={METRIC_EXPLANATIONS.precision}>
                      <Box
                        textAlign="center"
                        minW="60px"
                        cursor="help"
                        p={1}
                        bg={
                          sortField === "precision" ? "blue.50" : "transparent"
                        }
                        borderWidth={sortField === "precision" ? "1px" : "0"}
                        borderColor="blue.200"
                      >
                        <Text
                          fontSize="xs"
                          color={
                            sortField === "precision" ? "blue.600" : "fg.muted"
                          }
                          mb={0.5}
                        >
                          Precision
                        </Text>
                        <Text
                          fontSize="sm"
                          fontWeight="medium"
                          color="fg.emphasis"
                        >
                          {model.avg_precision !== null
                            ? model.avg_precision.toFixed(2)
                            : "-"}
                        </Text>
                      </Box>
                    </SimpleTooltip>

                    {/* Recall */}
                    <SimpleTooltip label={METRIC_EXPLANATIONS.recall}>
                      <Box
                        textAlign="center"
                        minW="55px"
                        cursor="help"
                        p={1}
                        bg={sortField === "recall" ? "blue.50" : "transparent"}
                        borderWidth={sortField === "recall" ? "1px" : "0"}
                        borderColor="blue.200"
                      >
                        <Text
                          fontSize="xs"
                          color={
                            sortField === "recall" ? "blue.600" : "fg.muted"
                          }
                          mb={0.5}
                        >
                          Recall
                        </Text>
                        <Text
                          fontSize="sm"
                          fontWeight="medium"
                          color="fg.emphasis"
                        >
                          {model.avg_recall !== null
                            ? model.avg_recall.toFixed(2)
                            : "-"}
                        </Text>
                      </Box>
                    </SimpleTooltip>

                    {/* F1 Score */}
                    <SimpleTooltip label={METRIC_EXPLANATIONS.f1Score}>
                      <Box
                        textAlign="center"
                        minW="45px"
                        cursor="help"
                        p={1}
                        bg={sortField === "f1" ? "blue.50" : "transparent"}
                        borderWidth={sortField === "f1" ? "1px" : "0"}
                        borderColor="blue.200"
                      >
                        <Text
                          fontSize="xs"
                          color={sortField === "f1" ? "blue.600" : "fg.muted"}
                          mb={0.5}
                        >
                          F1
                        </Text>
                        <Text
                          fontSize="sm"
                          fontWeight="medium"
                          color="fg.emphasis"
                        >
                          {model.avg_f1_score !== null
                            ? model.avg_f1_score.toFixed(2)
                            : "-"}
                        </Text>
                      </Box>
                    </SimpleTooltip>

                    {/* Reasoning Accuracy */}
                    <SimpleTooltip
                      label={METRIC_EXPLANATIONS.reasoningAccuracy}
                    >
                      <Box
                        textAlign="center"
                        minW="70px"
                        cursor="help"
                        p={1}
                        bg={
                          sortField === "reasoning" ? "blue.50" : "transparent"
                        }
                        borderWidth={sortField === "reasoning" ? "1px" : "0"}
                        borderColor="blue.200"
                      >
                        <HStack gap={1} justify="center" mb={0.5}>
                          <Icon
                            as={Brain}
                            boxSize={3}
                            color={
                              sortField === "reasoning"
                                ? "blue.500"
                                : "purple.400"
                            }
                          />
                          <Text
                            fontSize="xs"
                            color={
                              sortField === "reasoning"
                                ? "blue.600"
                                : "fg.muted"
                            }
                          >
                            Reasoning
                          </Text>
                        </HStack>
                        <Text
                          fontSize="sm"
                          fontWeight="medium"
                          color={
                            model.avg_reasoning_accuracy !== null
                              ? "purple.600"
                              : "gray.400"
                          }
                        >
                          {model.avg_reasoning_accuracy !== null
                            ? `${(model.avg_reasoning_accuracy * 100).toFixed(0)}%`
                            : "-"}
                        </Text>
                      </Box>
                    </SimpleTooltip>

                    {/* Execution Time */}
                    <Box
                      textAlign="center"
                      minW="55px"
                      p={1}
                      bg={sortField === "time" ? "blue.50" : "transparent"}
                      borderWidth={sortField === "time" ? "1px" : "0"}
                      borderColor="blue.200"
                    >
                      <Text
                        fontSize="xs"
                        color={sortField === "time" ? "blue.600" : "fg.muted"}
                        mb={0.5}
                      >
                        Time
                      </Text>
                      <Text
                        fontSize="sm"
                        fontWeight="medium"
                        color="fg.emphasis"
                      >
                        {model.avg_execution_time !== null
                          ? `${model.avg_execution_time.toFixed(1)}s`
                          : "-"}
                      </Text>
                    </Box>
                  </HStack>

                  {/* Expand Icon */}
                  <IconButton
                    aria-label="Expand"
                    size="sm"
                    variant="ghost"
                    color="gray.400"
                  >
                    <Icon
                      as={
                        expandedModel === getModelKey(model)
                          ? ChevronUp
                          : ChevronDown
                      }
                      boxSize={4}
                    />
                  </IconButton>
                </Flex>

                {/* Expanded Details */}
                <Collapsible.Root open={expandedModel === getModelKey(model)}>
                  <Collapsible.Content>
                    <Box
                      px={4}
                      pb={4}
                      pt={2}
                      borderTop="1px"
                      borderColor="gray.100"
                      bg="gray.50"
                    >
                      {/* Extended Metrics */}
                      {(model.avg_precision !== null ||
                        model.avg_recall !== null ||
                        model.avg_f1_score !== null) && (
                        <HStack gap={6} mb={4}>
                          {model.avg_precision !== null && (
                            <SimpleTooltip
                              label={METRIC_EXPLANATIONS.precision}
                            >
                              <Box cursor="help">
                                <HStack gap={1}>
                                  <Text fontSize="xs" color="fg.muted">
                                    Precision
                                  </Text>
                                  <Icon
                                    as={Info}
                                    boxSize={3}
                                    color="gray.400"
                                  />
                                </HStack>
                                <Text
                                  fontSize="lg"
                                  fontWeight="semibold"
                                  color="fg.emphasis"
                                >
                                  {model.avg_precision.toFixed(2)}
                                </Text>
                              </Box>
                            </SimpleTooltip>
                          )}
                          {model.avg_recall !== null && (
                            <SimpleTooltip label={METRIC_EXPLANATIONS.recall}>
                              <Box cursor="help">
                                <HStack gap={1}>
                                  <Text fontSize="xs" color="fg.muted">
                                    Recall
                                  </Text>
                                  <Icon
                                    as={Info}
                                    boxSize={3}
                                    color="gray.400"
                                  />
                                </HStack>
                                <Text
                                  fontSize="lg"
                                  fontWeight="semibold"
                                  color="fg.emphasis"
                                >
                                  {model.avg_recall.toFixed(2)}
                                </Text>
                              </Box>
                            </SimpleTooltip>
                          )}
                          {model.avg_f1_score !== null && (
                            <SimpleTooltip label={METRIC_EXPLANATIONS.f1Score}>
                              <Box cursor="help">
                                <HStack gap={1}>
                                  <Text fontSize="xs" color="fg.muted">
                                    F1 Score
                                  </Text>
                                  <Icon
                                    as={Info}
                                    boxSize={3}
                                    color="gray.400"
                                  />
                                </HStack>
                                <Text
                                  fontSize="lg"
                                  fontWeight="semibold"
                                  color="fg.emphasis"
                                >
                                  {model.avg_f1_score.toFixed(2)}
                                </Text>
                              </Box>
                            </SimpleTooltip>
                          )}
                        </HStack>
                      )}

                      {/* Run IDs */}
                      {model.run_ids && model.run_ids.length > 0 && (
                        <Box>
                          <Text fontSize="xs" color="fg.muted" mb={2}>
                            Runs ({model.run_ids.length})
                          </Text>
                          <Flex flexWrap="wrap" gap={2}>
                            {model.run_ids.slice(0, 10).map((runId) => (
                              <Button
                                key={runId}
                                size="xs"
                                variant="outline"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (onLoadRun) onLoadRun(runId);
                                }}
                                fontFamily="mono"
                              >
                                {runId.slice(0, 12)}...
                              </Button>
                            ))}
                            {model.run_ids.length > 10 && (
                              <Text
                                fontSize="xs"
                                color="fg.muted"
                                alignSelf="center"
                              >
                                +{model.run_ids.length - 10} more
                              </Text>
                            )}
                          </Flex>
                        </Box>
                      )}
                    </Box>
                  </Collapsible.Content>
                </Collapsible.Root>
              </Box>
            </Box>
          </MotionBox>
        ))}
      </VStack>
    </VStack>
  );
}
