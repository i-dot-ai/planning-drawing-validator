import React, { memo, useState, useCallback } from "react";
import {
  Box,
  Flex,
  HStack,
  Button,
  Text,
  Icon,
  Badge,
  Stack,
  Collapsible,
  RadioGroup,
  Menu,
  Portal,
} from "@chakra-ui/react";
import {
  Filter,
  ChevronDown,
  Download,
  FileJson,
  FileSpreadsheet,
  RotateCcw,
} from "lucide-react";
import { DocumentEvaluation } from "@/types";
import { LiveMetrics } from "@/hooks/useMetrics";

// ─────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────

export interface FilterState {
  expectedValidity: "all" | "VALID" | "INVALID";
  predictedValidity: "all" | "VALID" | "INVALID";
  correctness: "all" | "correct" | "incorrect";
  reasoningQuality: "all" | "none" | "low" | "medium" | "high";
}

export const DEFAULT_FILTERS: FilterState = {
  expectedValidity: "all",
  predictedValidity: "all",
  correctness: "all",
  reasoningQuality: "all",
};

export interface RunInfo {
  runId?: string;
  modelName?: string;
  reasoningEffort?: string;
  startTime?: string;
}

interface FilterPanelProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  totalCount: number;
  filteredCount: number;
  filteredDocuments: DocumentEvaluation[];
  runId?: string;
  metrics?: LiveMetrics;
  runInfo?: RunInfo;
}

// ─────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────

const countActiveFilters = (filters: FilterState): number => {
  let count = 0;
  if (filters.expectedValidity !== "all") count++;
  if (filters.predictedValidity !== "all") count++;
  if (filters.correctness !== "all") count++;
  if (filters.reasoningQuality !== "all") count++;
  return count;
};

// ─────────────────────────────────────────────────
// FILTER SECTION COMPONENT
// ─────────────────────────────────────────────────

interface FilterSectionProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}

const FilterSection = memo(function FilterSection({
  label,
  value,
  onChange,
  options,
}: FilterSectionProps) {
  return (
    <Box>
      <Text
        fontSize="xs"
        fontWeight="medium"
        color="gray.500"
        textTransform="uppercase"
        letterSpacing="wide"
        mb={2}
      >
        {label}
      </Text>
      <RadioGroup.Root
        value={value}
        onValueChange={(e: { value: string | null }) =>
          e.value && onChange(e.value)
        }
      >
        <Stack gap={1}>
          {options.map((option) => (
            <RadioGroup.Item
              key={option.value}
              value={option.value}
              cursor="pointer"
            >
              <RadioGroup.ItemHiddenInput />
              <RadioGroup.ItemControl />
              <RadioGroup.ItemText fontSize="sm" color="gray.700">
                {option.label}
              </RadioGroup.ItemText>
            </RadioGroup.Item>
          ))}
        </Stack>
      </RadioGroup.Root>
    </Box>
  );
});

// ─────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────

export const FilterPanel = memo(function FilterPanel({
  filters,
  onChange,
  totalCount,
  filteredCount,
  filteredDocuments,
  runId,
  metrics,
  runInfo,
}: FilterPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const activeCount = countActiveFilters(filters);
  const hasActiveFilters = activeCount > 0;

  const updateFilter = useCallback(
    <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
      onChange({ ...filters, [key]: value });
    },
    [filters, onChange],
  );

  const resetFilters = useCallback(() => {
    onChange(DEFAULT_FILTERS);
  }, [onChange]);

  // ─────────────────────────────────────────────────
  // EXPORT FUNCTIONS
  // ─────────────────────────────────────────────────

  const exportAsJSON = useCallback(() => {
    const exportData = {
      exported_at: new Date().toISOString(),
      run_id: runId || runInfo?.runId || "unknown",
      run_info: {
        model_name: runInfo?.modelName || null,
        reasoning_effort: runInfo?.reasoningEffort || null,
        start_time: runInfo?.startTime || null,
      },
      statistics: metrics
        ? {
            total_documents: totalCount,
            completed_documents: metrics.count,
            ground_truth_count: metrics.groundTruthCount,
            valid_predictions: metrics.validCount,
            invalid_predictions: metrics.invalidCount,
            confusion_matrix: {
              true_positives: metrics.tp,
              true_negatives: metrics.tn,
              false_positives: metrics.fp,
              false_negatives: metrics.fn,
            },
            accuracy: metrics.accuracy,
            precision: metrics.precision,
            recall: metrics.recall,
            f1_score: metrics.f1Score,
            avg_execution_time: metrics.avgTime,
            avg_classification_time: metrics.avgClassificationTime,
            avg_validation_time: metrics.avgValidationTime,
            avg_reasoning_score: metrics.avgReasoningScore,
            reasoning_evaluated_count: metrics.reasoningEvaluatedCount,
          }
        : null,
      filters_applied: filters,
      exported_documents: filteredCount,
      documents: filteredDocuments.map((doc) => ({
        document_id: doc.document_id,
        filename: doc.filename,
        expected_validity: doc.expected_validity,
        status: doc.status,
        predicted_validity: doc.final_result?.predicted_validity,
        predicted_reasoning: doc.final_result?.predicted_reasoning,
        confidence: doc.final_result?.confidence,
        correct: doc.final_result?.correct,
        execution_time: doc.final_result?.execution_time,
        prompt_type: doc.final_result?.prompt_type,
        reasoning_evaluated: doc.final_result?.reasoning_evaluated,
        reasoning_match_score: doc.final_result?.reasoning_match_score,
        reasoning_explanation: doc.final_result?.reasoning_explanation,
        carbon_impact: doc.final_result?.carbon_impact,
        stages: doc.stages,
      })),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `evaluation-export-${runId || "filtered"}-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [
    filteredDocuments,
    filters,
    filteredCount,
    totalCount,
    runId,
    metrics,
    runInfo,
  ]);

  const exportAsCSV = useCallback(() => {
    const headers = [
      "document_id",
      "filename",
      "expected_validity",
      "predicted_validity",
      "correct",
      "confidence",
      "execution_time",
      "reasoning_evaluated",
      "reasoning_match_score",
      "predicted_reasoning",
    ];

    const rows = filteredDocuments.map((doc) => [
      doc.document_id,
      doc.filename,
      doc.expected_validity,
      doc.final_result?.predicted_validity || "",
      doc.final_result?.correct ? "true" : "false",
      doc.final_result?.confidence || "",
      doc.final_result?.execution_time?.toFixed(2) || "",
      doc.final_result?.reasoning_evaluated ? "true" : "false",
      doc.final_result?.reasoning_match_score?.toFixed(4) || "",
      `"${(doc.final_result?.predicted_reasoning || "").replace(/"/g, '""').replace(/\n/g, " ")}"`,
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `evaluation-export-${runId || "filtered"}-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [filteredDocuments, runId]);

  // ─────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────

  return (
    <Box>
      {/* Toggle Bar */}
      <Flex align="center" justify="space-between" gap={3}>
        {/* Left: Count */}
        <Text fontSize="sm" color="gray.500">
          {filteredCount === totalCount
            ? `${totalCount} documents`
            : `${filteredCount} of ${totalCount} documents`}
        </Text>

        {/* Right: Actions */}
        <HStack gap={2}>
          {/* Filter Toggle */}
          <Button
            size="sm"
            variant={hasActiveFilters ? "solid" : "outline"}
            colorPalette={hasActiveFilters ? "gray" : undefined}
            bg={hasActiveFilters ? "gray.900" : undefined}
            color={hasActiveFilters ? "white" : "gray.600"}
            onClick={() => setIsOpen(!isOpen)}
            fontWeight="medium"
            _hover={{
              bg: hasActiveFilters ? "gray.800" : "gray.100",
            }}
          >
            <Icon as={Filter} boxSize={4} mr={2} />
            Filters
            {activeCount > 0 && (
              <Badge
                ml={1.5}
                bg="white"
                color="gray.900"
                fontSize="xs"
                borderRadius="full"
                px={1.5}
                minW={5}
              >
                {activeCount}
              </Badge>
            )}
            <Icon
              as={ChevronDown}
              boxSize={4}
              ml={2}
              transform={isOpen ? "rotate(180deg)" : undefined}
              transition="transform 0.15s ease"
            />
          </Button>

          {/* Export Menu */}
          {filteredCount > 0 && (
            <Menu.Root>
              <Menu.Trigger asChild>
                <Button
                  size="sm"
                  variant="outline"
                  color="gray.600"
                  fontWeight="medium"
                >
                  <Icon as={Download} boxSize={4} mr={2} />
                  Export
                  <Icon as={ChevronDown} boxSize={4} ml={2} />
                </Button>
              </Menu.Trigger>
              <Portal>
                <Menu.Positioner>
                  <Menu.Content
                    minW="160px"
                    py={1}
                    shadow="lg"
                    borderRadius="lg"
                  >
                    <Menu.Item
                      value="json"
                      onClick={exportAsJSON}
                      fontSize="sm"
                    >
                      <Icon as={FileJson} boxSize={4} mr={2} />
                      Export as JSON
                    </Menu.Item>
                    <Menu.Item value="csv" onClick={exportAsCSV} fontSize="sm">
                      <Icon as={FileSpreadsheet} boxSize={4} mr={2} />
                      Export as CSV
                    </Menu.Item>
                  </Menu.Content>
                </Menu.Positioner>
              </Portal>
            </Menu.Root>
          )}
        </HStack>
      </Flex>

      {/* Collapsible Filter Panel */}
      <Collapsible.Root open={isOpen}>
        <Collapsible.Content asChild>
          <Box
            mt={3}
            p={4}
            bg="gray.50"
            borderRadius="lg"
            border="1px solid"
            borderColor="gray.200"
          >
            {/* Filter Grid */}
            <Flex gap={6} flexWrap="wrap">
              {/* Result Filter */}
              <FilterSection
                label="Result"
                value={filters.correctness}
                onChange={(v) =>
                  updateFilter("correctness", v as FilterState["correctness"])
                }
                options={[
                  { value: "all", label: "All" },
                  { value: "correct", label: "Correct" },
                  { value: "incorrect", label: "Incorrect" },
                ]}
              />

              {/* Label Filter */}
              <FilterSection
                label="Label"
                value={filters.expectedValidity}
                onChange={(v) =>
                  updateFilter(
                    "expectedValidity",
                    v as FilterState["expectedValidity"],
                  )
                }
                options={[
                  { value: "all", label: "All" },
                  { value: "VALID", label: "Valid" },
                  { value: "INVALID", label: "Invalid" },
                ]}
              />

              {/* Predicted Filter */}
              <FilterSection
                label="Predicted"
                value={filters.predictedValidity}
                onChange={(v) =>
                  updateFilter(
                    "predictedValidity",
                    v as FilterState["predictedValidity"],
                  )
                }
                options={[
                  { value: "all", label: "All" },
                  { value: "VALID", label: "Valid" },
                  { value: "INVALID", label: "Invalid" },
                ]}
              />

              {/* Reasoning Quality Filter */}
              <FilterSection
                label="Reasoning"
                value={filters.reasoningQuality}
                onChange={(v) =>
                  updateFilter(
                    "reasoningQuality",
                    v as FilterState["reasoningQuality"],
                  )
                }
                options={[
                  { value: "all", label: "All" },
                  { value: "none", label: "No evaluation" },
                  { value: "low", label: "Low (<50%)" },
                  { value: "medium", label: "Medium (50-80%)" },
                  { value: "high", label: "High (≥80%)" },
                ]}
              />
            </Flex>

            {/* Reset Button */}
            {hasActiveFilters && (
              <Flex
                justify="flex-end"
                mt={4}
                pt={3}
                borderTop="1px solid"
                borderColor="gray.200"
              >
                <Button
                  size="sm"
                  variant="ghost"
                  color="gray.600"
                  onClick={resetFilters}
                  fontWeight="medium"
                  _hover={{ bg: "gray.100" }}
                >
                  <Icon as={RotateCcw} boxSize={4} mr={2} />
                  Reset all filters
                </Button>
              </Flex>
            )}
          </Box>
        </Collapsible.Content>
      </Collapsible.Root>
    </Box>
  );
});

export default FilterPanel;
