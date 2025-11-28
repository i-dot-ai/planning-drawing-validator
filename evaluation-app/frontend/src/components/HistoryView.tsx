import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  Clock,
  PlayCircle,
  CheckCircle2,
  AlertCircle,
  FileText,
  Trash2,
  Edit2,
  Check,
  X,
  Filter,
  BarChart3,
  Target,
  Download,
} from "lucide-react";
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
  Checkbox,
  Input,
  IconButton,
  Spinner,
  Progress,
  Separator,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { formatRelativeDate, pluralise } from "@/lib/utils";
import { api } from "@/lib/api";
import { SearchBar } from "./SearchBar";
import { EvaluationRun } from "@/types";
import { presets } from "@/lib/design-tokens";

// Create motion components
const MotionBox = motion.div;

interface HistoryViewProps {
  onLoadRun: (runId: string) => void;
  onResumeRun: (runId: string) => void;
}

export function HistoryView({ onLoadRun, onResumeRun }: HistoryViewProps) {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [showCompletedOnly, setShowCompletedOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState<string>("");

  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    try {
      const data = await api.runs.getRuns();
      setRuns(data.runs);
    } catch (error) {
      console.error("Failed to load runs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRunName = async (runId: string, newName: string) => {
    try {
      await api.runs.updateRunName(runId, newName);
      // Update local state
      setRuns(
        runs.map((run) =>
          run.run_id === runId ? { ...run, name: newName } : run,
        ),
      );
    } catch (error) {
      console.error("Failed to update run name:", error);
    }
  };

  const toggleSelection = (runId: string) => {
    setSelectedRuns((prev) => {
      const next = new Set(prev);
      if (next.has(runId)) {
        next.delete(runId);
      } else {
        next.add(runId);
      }
      return next;
    });
  };

  const selectAll = () => {
    setIsSelectionMode(true);
    setSelectedRuns(new Set(runs.map((r) => r.run_id)));
  };

  const clearSelection = () => {
    setSelectedRuns(new Set());
    setIsSelectionMode(false);
  };

  const enterSelectionMode = () => {
    setIsSelectionMode(true);
  };

  const deleteSelected = async () => {
    if (selectedRuns.size === 0) return;

    const confirmed = window.confirm(
      `Delete ${selectedRuns.size} ${pluralise(selectedRuns.size, "run")}?`,
    );

    if (!confirmed) return;

    try {
      await api.runs.deleteRuns(Array.from(selectedRuns));
      await loadRuns();
      setSelectedRuns(new Set());
      setIsSelectionMode(false);
    } catch (error) {
      console.error("Failed to delete runs:", error);
      toast.error("Failed to delete some runs. Check console for details.");
    }
  };

  const calculateCombinedStats = () => {
    const selected = runs.filter((r) => selectedRuns.has(r.run_id));
    if (selected.length === 0) return null;

    const totalDocs = selected.reduce(
      (sum, r) => sum + r.completed_documents,
      0,
    );
    const avgAccuracy = selected
      .filter((r) => r.accuracy !== undefined)
      .reduce((sum, r, _, arr) => sum + (r.accuracy || 0) / arr.length, 0);
    const avgTime = selected
      .filter((r) => r.execution_time !== undefined)
      .reduce(
        (sum, r, _, arr) => sum + (r.execution_time || 0) / arr.length,
        0,
      );

    return {
      runs: selected.length,
      totalDocs,
      avgAccuracy: avgAccuracy || null,
      avgTime: avgTime || null,
    };
  };

  const combinedStats = calculateCombinedStats();

  const calculateOverallStats = () => {
    const relevantRuns = showCompletedOnly
      ? runs.filter((r) => r.status === "completed")
      : runs;

    if (relevantRuns.length === 0) return null;

    const totalDocs = relevantRuns.reduce(
      (sum, r) => sum + r.completed_documents,
      0,
    );
    const avgAccuracy = relevantRuns
      .filter((r) => r.accuracy !== undefined)
      .reduce((sum, r, _, arr) => sum + (r.accuracy || 0) / arr.length, 0);
    const avgTime = relevantRuns
      .filter((r) => r.execution_time !== undefined)
      .reduce(
        (sum, r, _, arr) => sum + (r.execution_time || 0) / arr.length,
        0,
      );

    return {
      totalRuns: relevantRuns.length,
      totalDocs,
      avgAccuracy: avgAccuracy || null,
      avgTime: avgTime || null,
    };
  };

  const overallStats = calculateOverallStats();

  // Filter runs based on completion status and search query
  const filteredRuns = runs.filter((run) => {
    // First apply completion filter
    if (showCompletedOnly && run.status !== "completed") {
      return false;
    }

    // Then apply search filter
    if (!searchQuery.trim()) return true;

    const query = searchQuery.toLowerCase();
    const runName = run.name?.toLowerCase() || "";
    const runId = run.run_id.toLowerCase();
    const accuracy = run.accuracy?.toString() || "";

    return (
      runName.includes(query) ||
      runId.includes(query) ||
      accuracy.includes(query) ||
      run.status.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return (
      <Flex align="center" justify="center" py={16}>
        <VStack gap={2}>
          <Spinner size="lg" color="gray.300" />
          <Text fontSize="sm" color="fg.muted">
            Loading history...
          </Text>
        </VStack>
      </Flex>
    );
  }

  if (runs.length === 0) {
    return (
      <Flex align="center" justify="center" py={16}>
        <VStack gap={2}>
          <Icon as={FileText} boxSize={8} color="gray.300" />
          <Text fontSize="sm" fontWeight="medium" color="fg.muted">
            No evaluation runs yet
          </Text>
          <Text fontSize="xs" color="gray.400">
            Start an evaluation to see it here
          </Text>
        </VStack>
      </Flex>
    );
  }

  return (
    <VStack gap={6} align="stretch">
      {/* Toolbar */}
      {runs.length > 0 && (
        <Card.Root
          borderRadius="lg"
          boxShadow="none"
          borderWidth="1px"
          borderColor="gray.200"
          position="relative"
          overflow="hidden"
        >
          {/* Visual indicator for toolbar */}
          <Box
            position="absolute"
            left={0}
            top={0}
            bottom={0}
            width="4px"
            bg="gray.900"
            borderLeftRadius="lg"
          />
          <Card.Body p={0}>
            <Flex h={14} align="center" justify="space-between" px={4}>
              <Flex align="center" gap={3} pl={2}>
                {!isSelectionMode ? (
                  <>
                    {/* Tools Label */}
                    <Text {...presets.sectionLabel}>Tools</Text>
                    <Separator
                      orientation="vertical"
                      h={6}
                      borderColor="gray.200"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={enterSelectionMode}
                      color="fg.muted"
                      fontWeight="medium"
                      _hover={{ bg: "gray.100" }}
                    >
                      <Icon as={CheckCircle2} mr={1.5} />
                      Select
                    </Button>
                    <Button
                      variant={showCompletedOnly ? "solid" : "ghost"}
                      size="sm"
                      onClick={() => setShowCompletedOnly(!showCompletedOnly)}
                      bg={showCompletedOnly ? "gray.900" : "transparent"}
                      color={showCompletedOnly ? "white" : "fg.muted"}
                      fontWeight="medium"
                      _hover={{
                        bg: showCompletedOnly ? "gray.800" : "gray.100",
                      }}
                      title={
                        showCompletedOnly
                          ? "Showing completed runs only"
                          : "Showing all runs"
                      }
                    >
                      <Icon as={Filter} mr={1.5} />
                      {showCompletedOnly ? "Completed" : "All"}
                    </Button>
                  </>
                ) : (
                  <>
                    <Flex align="center" gap={3}>
                      <Checkbox.Root
                        checked={
                          selectedRuns.size === runs.length && runs.length > 0
                        }
                        onCheckedChange={(e: {
                          checked: boolean | "indeterminate";
                        }) => (e.checked ? selectAll() : clearSelection())}
                        colorPalette="gray"
                      >
                        <Checkbox.HiddenInput />
                        <Checkbox.Control />
                      </Checkbox.Root>
                      <Text fontSize="sm" color="fg.muted">
                        {selectedRuns.size > 0
                          ? `${selectedRuns.size} selected`
                          : "Select all"}
                      </Text>
                    </Flex>

                    {selectedRuns.size > 0 && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={deleteSelected}
                        color="fg.muted"
                        _hover={{ bg: "gray.100" }}
                      >
                        <Icon as={Trash2} mr={1.5} />
                        Delete
                      </Button>
                    )}

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearSelection}
                      color="fg.muted"
                      _hover={{ bg: "gray.100" }}
                    >
                      Cancel
                    </Button>
                  </>
                )}
              </Flex>

              {combinedStats && selectedRuns.size > 1 && (
                <Flex align="center" gap={4} fontSize="sm" color="gray.500">
                  <Text fontWeight="medium" color="fg.emphasis">
                    {combinedStats.runs} runs
                  </Text>
                  <Text>{combinedStats.totalDocs} docs</Text>
                  {combinedStats.avgAccuracy && (
                    <Text>
                      {combinedStats.avgAccuracy.toFixed(0)}% avg accuracy
                    </Text>
                  )}
                  {combinedStats.avgTime && (
                    <Text>{combinedStats.avgTime.toFixed(1)}s avg time</Text>
                  )}
                </Flex>
              )}
            </Flex>
          </Card.Body>
        </Card.Root>
      )}

      {/* Overall Statistics */}
      {overallStats && (
        <Card.Root
          borderRadius="lg"
          boxShadow="none"
          borderWidth="1px"
          borderColor="gray.200"
          position="relative"
          overflow="hidden"
        >
          {/* Visual indicator for stats */}
          <Box
            position="absolute"
            left={0}
            top={0}
            bottom={0}
            width="4px"
            bg="gray.200"
            borderLeftRadius="lg"
            zIndex={20}
          />
          <Card.Body p={0}>
            <Flex h={16} align="center" overflowX="auto">
              {/* Stats Label */}
              <Box
                position="sticky"
                left={0}
                bg="white"
                pl={5}
                pr={4}
                zIndex={10}
              >
                <Text {...presets.sectionLabel}>Stats</Text>
              </Box>
              <HStack gap={0} divideX="1px" divideColor="gray.100">
                <MetricDisplay
                  label="Total Runs"
                  value={overallStats.totalRuns}
                  icon={BarChart3}
                />
                <MetricDisplay
                  label="Total Documents"
                  value={overallStats.totalDocs}
                  icon={FileText}
                />
                <MetricDisplay
                  label="Avg Accuracy"
                  value={
                    overallStats.avgAccuracy !== null
                      ? `${overallStats.avgAccuracy.toFixed(0)}%`
                      : "—"
                  }
                  icon={Target}
                />
                <MetricDisplay
                  label="Avg Time"
                  value={
                    overallStats.avgTime !== null
                      ? `${overallStats.avgTime.toFixed(1)}s`
                      : "—"
                  }
                  icon={Clock}
                />
              </HStack>
            </Flex>
          </Card.Body>
        </Card.Root>
      )}

      {/* Title and Search */}
      <VStack gap={5} align="stretch">
        <Flex align="center" justify="space-between">
          <Box>
            <Text fontSize="lg" fontWeight="semibold" color="fg.emphasis">
              Evaluation Runs
            </Text>
            <Text mt={0.5} fontSize="sm" color="fg.muted">
              Showing {filteredRuns.length} of {runs.length}{" "}
              {runs.length === 1 ? "run" : "runs"}
            </Text>
          </Box>
          <Box width="384px">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Search runs, status, accuracy..."
            />
          </Box>
        </Flex>

        {/* Runs List */}
        <VStack gap={3} align="stretch">
          {filteredRuns.map((run, index) => (
            <MotionBox
              key={run.run_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
            >
              <RunCard
                run={run}
                isSelectionMode={isSelectionMode}
                isSelected={selectedRuns.has(run.run_id)}
                onToggleSelect={() => toggleSelection(run.run_id)}
                onLoad={() => onLoadRun(run.run_id)}
                onResume={() => onResumeRun(run.run_id)}
                onUpdateName={handleUpdateRunName}
                onDelete={async () => {
                  const confirmed = window.confirm("Delete this run?");
                  if (confirmed) {
                    try {
                      await api.runs.deleteRun(run.run_id);
                      await loadRuns();
                    } catch (error) {
                      console.error("Failed to delete run:", error);
                    }
                  }
                }}
              />
            </MotionBox>
          ))}
        </VStack>
      </VStack>
    </VStack>
  );
}

interface MetricDisplayProps {
  label: string;
  value: string | number;
  icon: React.ElementType;
}

function MetricDisplay({ label, value, icon }: MetricDisplayProps) {
  return (
    <Flex align="center" gap={3} px={6}>
      <Flex
        align="center"
        justify="center"
        boxSize={10}
        borderRadius="lg"
        bg="gray.50"
      >
        <Icon as={icon} boxSize={4} color="gray.600" />
      </Flex>
      <Box>
        <Text fontSize="xs" color="fg.muted" fontWeight="medium">
          {label}
        </Text>
        <Text fontSize="lg" fontWeight="semibold" color="fg.emphasis">
          {value}
        </Text>
      </Box>
    </Flex>
  );
}

interface RunCardProps {
  run: EvaluationRun;
  isSelectionMode: boolean;
  isSelected: boolean;
  onToggleSelect: () => void;
  onLoad: () => void;
  onResume: () => void;
  onDelete: () => void;
  onUpdateName: (runId: string, newName: string) => Promise<void>;
}

function RunCard({
  run,
  isSelectionMode,
  isSelected,
  onToggleSelect,
  onLoad,
  onResume,
  onDelete,
  onUpdateName,
}: RunCardProps) {
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState(run.name || "");
  const isCompleted = run.status === "completed";
  const isRunning = run.status === "running";
  const isIncomplete =
    !isCompleted && run.completed_documents < run.total_documents;
  const progress =
    run.total_documents > 0
      ? (run.completed_documents / run.total_documents) * 100
      : 0;

  const handleSaveName = async () => {
    await onUpdateName(run.run_id, editedName);
    setIsEditingName(false);
  };

  const handleCancelEdit = () => {
    setEditedName(run.name || "");
    setIsEditingName(false);
  };

  return (
    <Card.Root
      borderRadius="lg"
      boxShadow="none"
      borderWidth="1px"
      borderColor={
        isSelected
          ? "gray.300"
          : isCompleted
            ? "gray.200"
            : isRunning
              ? "gray.300"
              : "gray.200"
      }
      bg={isRunning ? "gray.50" : isIncomplete ? "gray.50/30" : "white"}
      position="relative"
      overflow="hidden"
      transition="all 0.15s ease"
      _hover={{ borderColor: "gray.300" }}
    >
      {/* Visual accent for run cards */}
      <Box
        position="absolute"
        left={0}
        top={0}
        bottom={0}
        width="2px"
        bg="purple.400"
        opacity={0.3}
      />
      <Card.Body p={0}>
        <Flex align="center" px={4} py={3}>
          {/* Checkbox - only takes space when visible */}
          {isSelectionMode && (
            <Box mr={4} onClick={(e) => e.stopPropagation()}>
              <Checkbox.Root
                checked={isSelected}
                onCheckedChange={onToggleSelect}
                colorPalette="gray"
              >
                <Checkbox.HiddenInput />
                <Checkbox.Control />
              </Checkbox.Root>
            </Box>
          )}

          {/* Run Info - Clickable */}
          <Flex flex={1} align="center" minW={0}>
            {/* Status Icon */}
            <Flex
              align="center"
              justify="center"
              boxSize={8}
              borderRadius="lg"
              flexShrink={0}
              mr={3}
              bg={
                isCompleted ? "gray.100" : isRunning ? "gray.900" : "gray.100"
              }
            >
              {isCompleted ? (
                <Icon as={CheckCircle2} boxSize={4} color="gray.600" />
              ) : isRunning ? (
                <Icon
                  as={Clock}
                  boxSize={4}
                  color="white"
                  animation="pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite"
                />
              ) : isIncomplete ? (
                <Icon as={AlertCircle} boxSize={4} color="gray.500" />
              ) : (
                <Icon as={FileText} boxSize={4} color="gray.400" />
              )}
            </Flex>

            {/* Run Info */}
            <Box flex={1} minW={0}>
              {isEditingName ? (
                <Flex align="center" gap={2}>
                  <Input
                    value={editedName}
                    onChange={(e) => setEditedName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSaveName();
                      if (e.key === "Escape") handleCancelEdit();
                    }}
                    size="sm"
                    fontSize="sm"
                    fontWeight="semibold"
                    borderRadius="sm"
                    borderColor="gray.300"
                    _focus={{
                      borderColor: "gray.400",
                      boxShadow: "0 0 0 1px var(--chakra-colors-gray-400)",
                    }}
                    placeholder="Run name..."
                    autoFocus
                  />
                  <IconButton
                    aria-label="Save"
                    size="sm"
                    variant="ghost"
                    onClick={handleSaveName}
                    color="fg.muted"
                    _hover={{ bg: "gray.100" }}
                  >
                    <Icon as={Check} />
                  </IconButton>
                  <IconButton
                    aria-label="Cancel"
                    size="sm"
                    variant="ghost"
                    onClick={handleCancelEdit}
                    color="fg.muted"
                    _hover={{ bg: "gray.100" }}
                  >
                    <Icon as={X} />
                  </IconButton>
                </Flex>
              ) : (
                <Box
                  as="button"
                  onClick={onLoad}
                  width="full"
                  textAlign="left"
                  transition="opacity 0.15s ease"
                  _hover={{ opacity: 0.7 }}
                >
                  <Flex align="center" gap={2}>
                    <Text
                      fontSize="sm"
                      fontWeight="semibold"
                      color="fg.emphasis"
                    >
                      {run.name ||
                        `Run · ${formatRelativeDate(run.start_time || run.timestamp)}`}
                    </Text>
                    {!isSelectionMode && (
                      <IconButton
                        aria-label="Edit name"
                        size="xs"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          setIsEditingName(true);
                        }}
                        color="gray.400"
                        opacity={0}
                        _groupHover={{ opacity: 1 }}
                        _hover={{ bg: "gray.100", color: "gray.600" }}
                      >
                        <Icon as={Edit2} boxSize={3} />
                      </IconButton>
                    )}
                    {run.accuracy !== undefined && (
                      <Badge
                        px={2}
                        py={0.5}
                        fontSize="xs"
                        fontWeight="medium"
                        {...presets.badgeNeutral}
                      >
                        {run.accuracy.toFixed(0)}%
                      </Badge>
                    )}
                    {run.model_name && (
                      <Badge
                        px={2}
                        py={0.5}
                        fontSize="xs"
                        fontWeight="medium"
                        bg="purple.50"
                        color="purple.600"
                        borderRadius="md"
                      >
                        {run.model_name}
                      </Badge>
                    )}
                    {run.reasoning_effort && (
                      <Badge
                        px={2}
                        py={0.5}
                        fontSize="xs"
                        fontWeight="medium"
                        {...presets.badgeWarning}
                      >
                        reasoning: {run.reasoning_effort}
                      </Badge>
                    )}
                  </Flex>
                  <Flex
                    align="center"
                    gap={3}
                    mt={1}
                    fontSize="xs"
                    color="fg.muted"
                  >
                    <Flex align="center" gap={1}>
                      <Icon as={FileText} boxSize={3} />
                      <Text fontWeight="medium">{run.completed_documents}</Text>
                      <Text color="gray.400">/</Text>
                      <Text>{run.total_documents} documents</Text>
                    </Flex>
                    {run.execution_time && (
                      <>
                        <Text color="gray.300">·</Text>
                        <Flex align="center" gap={1}>
                          <Icon as={Clock} boxSize={3} />
                          {run.execution_time.toFixed(1)}s
                        </Flex>
                      </>
                    )}
                    {isIncomplete && (
                      <>
                        <Text color="gray.300">·</Text>
                        <Text fontWeight="medium" color="gray.700">
                          {progress.toFixed(0)}% complete
                        </Text>
                      </>
                    )}
                  </Flex>
                </Box>
              )}
            </Box>
          </Flex>

          {/* Action Buttons - hide in selection mode */}
          {!isSelectionMode && (
            <Flex ml={4} gap={2} flexShrink={0}>
              {isIncomplete && (
                <Button
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onResume();
                  }}
                  bg="gray.900"
                  color="white"
                  fontSize="xs"
                  fontWeight="medium"
                  borderRadius="sm"
                  _hover={{ bg: "gray.800" }}
                >
                  <Icon as={PlayCircle} mr={1.5} />
                  Resume
                </Button>
              )}

              <IconButton
                aria-label="Export run data"
                size="sm"
                variant="ghost"
                onClick={async (e) => {
                  e.stopPropagation();
                  try {
                    const data = await api.runs.exportRun(run.run_id);
                    const blob = new Blob([JSON.stringify(data, null, 2)], {
                      type: "application/json",
                    });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `${run.run_id}_export.json`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    toast.success("Export downloaded successfully");
                  } catch (error) {
                    console.error("Failed to export run:", error);
                    toast.error("Failed to export run");
                  }
                }}
                color="gray.400"
                _hover={{ bg: "gray.100", color: "gray.600" }}
              >
                <Icon as={Download} boxSize={3.5} />
              </IconButton>

              <IconButton
                aria-label="Delete run"
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete();
                }}
                color="gray.400"
                _hover={{ bg: "gray.100", color: "gray.600" }}
              >
                <Icon as={Trash2} boxSize={3.5} />
              </IconButton>
            </Flex>
          )}
        </Flex>

        {/* Progress bar for incomplete runs */}
        {isIncomplete && (
          <Box px={4} pb={3}>
            <Progress.Root value={progress} size="xs" colorPalette="gray">
              <Progress.Track borderRadius="full" bg="gray.200/50">
                <Progress.Range />
              </Progress.Track>
            </Progress.Root>
          </Box>
        )}
      </Card.Body>
    </Card.Root>
  );
}
