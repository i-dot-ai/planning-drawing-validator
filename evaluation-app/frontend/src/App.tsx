import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  lazy,
  Suspense,
} from "react";
import { Box, Container, VStack, Heading, Text, Flex } from "@chakra-ui/react";
import { Toaster, toast } from "sonner";
import { layout } from "@/lib/design-tokens";
import { Header } from "./components/Header";
import { SearchBar } from "./components/SearchBar";
import { LiveMetrics } from "./components/LiveMetrics";
import { DocumentCard } from "./components/DocumentCard";
import { DocumentQueue } from "./components/DocumentQueue";
import { EmptyState } from "./components/EmptyState";
import { GettingStarted } from "./components/GettingStarted";
import { ReadyQueue } from "./components/ReadyQueue";
import {
  FilterPanel,
  FilterState,
  DEFAULT_FILTERS,
} from "./components/FilterPanel";
import { LoadingSpinner } from "./components/LoadingSpinner";
import { RunHeader } from "./components/RunHeader";
import { RunConfigModal, RunConfig } from "./components/RunConfigModal";
import { useWebSocket } from "./hooks/useWebSocket";
import { useEvaluation } from "./hooks/useEvaluation";
import { DocumentInfo } from "./types";

// Lazy load large components for better performance
const HistoryView = lazy(() =>
  import("./components/HistoryView").then((module) => ({
    default: module.HistoryView,
  })),
);
const PromptsView = lazy(() =>
  import("./components/PromptsView").then((module) => ({
    default: module.PromptsView,
  })),
);
const ModelComparisonView = lazy(() =>
  import("./components/ModelComparisonView").then((module) => ({
    default: module.ModelComparisonView,
  })),
);

const App: React.FC = () => {
  const [viewMode, setViewMode] = useState<
    "run" | "history" | "prompts" | "compare"
  >("run");
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [selectedDocument, setSelectedDocument] = useState<string>("");
  const [loadedRunInfo, setLoadedRunInfo] = useState<{
    run_id: string;
    start_time: string;
    accuracy?: number;
    model_name?: string;
  } | null>(null);
  const [showConfigModal, setShowConfigModal] = useState<boolean>(false);
  const [dataDir, setDataDir] = useState<string>("");
  const [groundTruthPath, setGroundTruthPath] = useState<string>("");
  const [groundTruthLabelCount, setGroundTruthLabelCount] = useState<number>(0);
  const [runConfig, setRunConfig] = useState<RunConfig>({
    maxSamples: null,
    concurrency: 10,
    documentIds: [],
    modelName: "",
    reasoningEffort: null,
    columnConfig: null,
  });

  const {
    evaluations,
    setEvaluations,
    isRunning,
    setIsRunning,
    currentRunId,
    documentQueue,
    queueStatus,
    handleWebSocketMessage,
    liveMetrics,
  } = useEvaluation();

  const { connectionStatus } = useWebSocket(handleWebSocketMessage);

  // Load documents and default model on mount
  useEffect(() => {
    loadDocuments();
    // Fetch default model
    fetch("/api/models")
      .then((res) => res.json())
      .then((data: { models: Array<{ id: string; is_default: boolean }> }) => {
        const defaultModel = data.models?.find((m) => m.is_default);
        if (defaultModel) {
          setRunConfig((prev) => ({ ...prev, modelName: defaultModel.id }));
        }
      })
      .catch(() => {});
    // Note: useEvaluation hook now handles loading current run
  }, []);

  // Load documents whenever dataDir changes
  useEffect(() => {
    if (dataDir) {
      loadDocuments();
    }
  }, [dataDir]);

  // Load ground truth label count when path changes
  useEffect(() => {
    const loadLabelCount = async () => {
      if (!groundTruthPath) {
        setGroundTruthLabelCount(0);
        return;
      }
      try {
        const response = await fetch(
          `/api/ground-truth?path=${encodeURIComponent(groundTruthPath)}`,
        );
        if (response.ok) {
          const data = await response.json();
          setGroundTruthLabelCount(data.entries?.length || 0);
        }
      } catch {
        // Silently ignore ground truth loading errors
      }
    };
    loadLabelCount();
  }, [groundTruthPath]);

  // Note: Queue is initialized when documents are loaded (in loadDocuments)
  // and when starting evaluation (in handleStartEvaluation)
  // We don't auto-repopulate after runs complete to keep the UI clean

  // Calculate cumulative carbon impact from all evaluations
  const cumulativeCarbonImpact = useMemo(() => {
    const docsWithImpact = evaluations.filter(
      (doc) => doc.final_result?.carbon_impact,
    );

    if (docsWithImpact.length === 0) return null;

    return docsWithImpact.reduce(
      (totals, doc) => {
        const impact = doc.final_result!.carbon_impact!;
        return {
          energy_kwh_min: totals.energy_kwh_min + impact.energy_kwh_min,
          energy_kwh_max: totals.energy_kwh_max + impact.energy_kwh_max,
          gwp_kgco2eq_min: totals.gwp_kgco2eq_min + impact.gwp_kgco2eq_min,
          gwp_kgco2eq_max: totals.gwp_kgco2eq_max + impact.gwp_kgco2eq_max,
          adpe_kgsbeq_min: totals.adpe_kgsbeq_min + impact.adpe_kgsbeq_min,
          adpe_kgsbeq_max: totals.adpe_kgsbeq_max + impact.adpe_kgsbeq_max,
          pe_mj_min: totals.pe_mj_min + impact.pe_mj_min,
          pe_mj_max: totals.pe_mj_max + impact.pe_mj_max,
          wcf_l_min: totals.wcf_l_min + impact.wcf_l_min,
          wcf_l_max: totals.wcf_l_max + impact.wcf_l_max,
        };
      },
      {
        energy_kwh_min: 0,
        energy_kwh_max: 0,
        gwp_kgco2eq_min: 0,
        gwp_kgco2eq_max: 0,
        adpe_kgsbeq_min: 0,
        adpe_kgsbeq_max: 0,
        pe_mj_min: 0,
        pe_mj_max: 0,
        wcf_l_min: 0,
        wcf_l_max: 0,
      },
    );
  }, [evaluations]);

  const loadDocuments = async () => {
    try {
      const response = await fetch("/api/documents");
      if (response.ok) {
        const data = await response.json();
        const docs = data.documents || [];
        setDocuments(docs);
        // Note: Queue is only populated when starting evaluation (in handleStartEvaluation)
      }
    } catch {
      // Silently ignore document loading errors
    }
  };

  const handleConfigSubmit = (config: RunConfig) => {
    setRunConfig(config);
  };

  const handleStartEvaluation = async () => {
    if (!dataDir) {
      return;
    }

    // Queue will be initialized automatically by WebSocket EVALUATION_STARTED message
    try {
      const requestBody = {
        max_samples: runConfig.maxSamples,
        concurrency: runConfig.concurrency,
        data_dir: dataDir,
        document_ids:
          runConfig.documentIds.length > 0 ? runConfig.documentIds : null,
        skip_ground_truth: !groundTruthPath,
        ground_truth_path: groundTruthPath || null,
        model_name: runConfig.modelName || null,
        reasoning_effort: runConfig.reasoningEffort || null,
        column_config: runConfig.columnConfig,
      };

      const response = await fetch("/api/start-evaluation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        setIsRunning(true);
      } else {
        const errorData = await response.json();
        toast.error(
          `Failed to start evaluation: ${errorData.detail || "Unknown error"}`,
        );
      }
    } catch {
      toast.error("Failed to start evaluation.");
    }
  };

  const handleStopEvaluation = async () => {
    try {
      const response = await fetch("/api/stop-evaluation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (response.ok) {
        setIsRunning(false);
      }
    } catch {
      // Silently ignore stop errors
    }
  };

  const handleReset = useCallback(() => {
    setEvaluations([]);
    setSelectedDocument("");
    setLoadedRunInfo(null);
    setDataDir("");
    setGroundTruthPath("");
    setDocuments([]);
    setFilters(DEFAULT_FILTERS);
    setSearchQuery("");
  }, [setEvaluations]);

  const handleToggleDocument = useCallback((documentId: string) => {
    setSelectedDocument((prev) => (prev === documentId ? "" : documentId));
  }, []);

  const handleLoadRun = useCallback(async (runId: string) => {
    try {
      const response = await fetch(`/api/runs/${runId}`);
      if (response.ok) {
        const data = await response.json();
        const completedDocs = (data.documents || []).map((doc: any) => ({
          document_id: doc.document_id,
          filename: doc.filename,
          expected_validity: doc.expected_validity || "Unknown",
          status: "completed" as const,
          stages: doc.stages || [
            {
              stage: 1,
              stage_name: "Classification",
              status: "completed" as const,
            },
            {
              stage: 2,
              stage_name: "Validation",
              status: "completed" as const,
            },
          ],
          final_result: {
            predicted_validity: doc.predicted_validity,
            predicted_reasoning: doc.predicted_reasoning,
            confidence: doc.confidence,
            correct: doc.is_correct,
            prompt_type: doc.prompt_type,
            execution_time: doc.execution_time,
            carbon_impact: doc.carbon_impact,
            reasoning_match_score: doc.reasoning_match_score,
            reasoning_evaluated: doc.reasoning_evaluated,
            reasoning_explanation: doc.reasoning_explanation,
          },
        }));
        setEvaluations(completedDocs);
        setLoadedRunInfo({
          run_id: data.run_id,
          start_time: data.start_time,
          accuracy: data.accuracy,
          model_name: data.model_name,
        });

        // Set run context info for header display
        if (data.data_dir) {
          setDataDir(data.data_dir);
        }

        setViewMode("run");
      }
    } catch {
      // Silently ignore load errors
    }
  }, []);

  const handleReloadCurrentRun = useCallback(async () => {
    const runId = loadedRunInfo?.run_id || currentRunId;
    if (runId) {
      await handleLoadRun(runId);
    }
  }, [loadedRunInfo?.run_id, currentRunId, handleLoadRun]);

  const handleResumeRun = async (runId: string) => {
    try {
      const response = await fetch("/api/resume-evaluation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_id: runId }),
      });

      if (response.ok) {
        setIsRunning(true);
        setViewMode("run");
      } else {
        const errorData = await response.json();
        toast.error(
          `Failed to resume evaluation: ${errorData.detail || "Unknown error"}`,
        );
      }
    } catch {
      toast.error("Failed to resume evaluation.");
    }
  };

  const handleGroundTruthUpdated = async (path: string, labelCount: number) => {
    // Update the ground truth path and label count directly
    setGroundTruthPath(path);
    setGroundTruthLabelCount(labelCount);

    // Determine run_id to reload
    const runId = loadedRunInfo?.run_id || currentRunId;

    // If we don't have a run_id, try to extract it from the ground truth path
    // Path format: runs/run_TIMESTAMP/ground_truth.json
    let effectiveRunId = runId;
    if (!effectiveRunId && path.includes("runs/")) {
      const match = path.match(/runs\/(run_[^/]+)/);
      if (match) {
        effectiveRunId = match[1];
      }
    }

    if (!effectiveRunId) {
      return;
    }

    // Add a small delay to ensure backend has finished updating the database
    await new Promise((resolve) => setTimeout(resolve, 500));

    try {
      const response = await fetch(`/api/runs/${effectiveRunId}`);

      if (!response.ok) {
        return;
      }

      const data = await response.json();

      const completedDocs = (data.documents || []).map((doc: any) => ({
        document_id: doc.document_id,
        filename: doc.filename,
        expected_validity: doc.expected_validity || "Unknown",
        status: "completed" as const,
        stages: doc.stages || [
          {
            stage: 1,
            stage_name: "Classification",
            status: "completed" as const,
          },
          { stage: 2, stage_name: "Validation", status: "completed" as const },
        ],
        final_result: {
          predicted_validity: doc.predicted_validity,
          predicted_reasoning: doc.predicted_reasoning,
          confidence: doc.confidence,
          correct: doc.is_correct,
          prompt_type: doc.prompt_type,
          execution_time: doc.execution_time,
          carbon_impact: doc.carbon_impact,
          reasoning_match_score: doc.reasoning_match_score,
          reasoning_evaluated: doc.reasoning_evaluated,
          reasoning_explanation: doc.reasoning_explanation,
        },
      }));

      setEvaluations(completedDocs);
    } catch {
      // Silently ignore reload errors
    }
  };

  // Filter evaluations based on search and filters (memoized to prevent unnecessary recalculations)
  const filteredEvaluations = useMemo(() => {
    return evaluations.filter((docEval) => {
      // Apply search query filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesSearch =
          docEval.filename.toLowerCase().includes(query) ||
          docEval.document_id.toLowerCase().includes(query) ||
          docEval.expected_validity.toLowerCase().includes(query) ||
          docEval.final_result?.predicted_validity
            ?.toLowerCase()
            .includes(query) ||
          docEval.final_result?.predicted_reasoning
            ?.toLowerCase()
            .includes(query) ||
          docEval.stages.some(
            (stage) =>
              stage.stage_name.toLowerCase().includes(query) ||
              stage.reasoning?.toLowerCase().includes(query),
          );
        if (!matchesSearch) return false;
      }

      // Apply correctness filter
      if (filters.correctness !== "all") {
        const isCorrect = docEval.final_result?.correct;
        if (filters.correctness === "correct" && !isCorrect) return false;
        if (filters.correctness === "incorrect" && isCorrect !== false)
          return false;
      }

      // Apply expected validity filter
      if (filters.expectedValidity !== "all") {
        if (docEval.expected_validity !== filters.expectedValidity)
          return false;
      }

      // Apply predicted validity filter
      if (filters.predictedValidity !== "all") {
        if (
          docEval.final_result?.predicted_validity !== filters.predictedValidity
        )
          return false;
      }

      // Apply reasoning quality filter
      if (filters.reasoningQuality !== "all") {
        const hasEval = docEval.final_result?.reasoning_evaluated === true;
        const score = docEval.final_result?.reasoning_match_score;
        const scorePercent = score != null ? score * 100 : null;

        switch (filters.reasoningQuality) {
          case "none":
            // Show only documents WITHOUT reasoning evaluation
            if (hasEval) return false;
            break;
          case "low":
            // Show documents WITH eval AND score < 50%
            if (!hasEval || scorePercent === null || scorePercent >= 50)
              return false;
            break;
          case "medium":
            // Show documents WITH eval AND score >= 50% AND < 80%
            if (
              !hasEval ||
              scorePercent === null ||
              scorePercent < 50 ||
              scorePercent >= 80
            )
              return false;
            break;
          case "high":
            // Show documents WITH eval AND score >= 80%
            if (!hasEval || scorePercent === null || scorePercent < 80)
              return false;
            break;
        }
      }

      return true;
    });
  }, [evaluations, searchQuery, filters]);

  return (
    <Box minH="100vh" bg="bg.canvas">
      <Header
        viewMode={viewMode}
        setViewMode={setViewMode}
        connectionStatus={connectionStatus}
        dataDir={dataDir}
        groundTruthPath={groundTruthPath}
        currentModelName={runConfig.modelName}
        onDataDirSelect={setDataDir}
        onGroundTruthSelect={handleGroundTruthUpdated}
        onOpenRunConfig={() => setShowConfigModal(true)}
        isRunning={isRunning}
        onStart={handleStartEvaluation}
        onStop={handleStopEvaluation}
        onReset={handleReset}
        loadedRunInfo={loadedRunInfo}
      />

      <Container
        maxW={layout.maxWidth.content}
        as="main"
        py={layout.containerPadding.y}
        px={layout.containerPadding.x}
      >
        {viewMode === "run" ? (
          <VStack gap={12} align="stretch">
            {/* Run Header - shown for historical runs */}
            {loadedRunInfo && (
              <RunHeader
                runId={loadedRunInfo.run_id}
                startTime={loadedRunInfo.start_time}
                accuracy={loadedRunInfo.accuracy}
                modelName={loadedRunInfo.model_name}
                totalDocuments={evaluations.length}
                cumulativeCarbonImpact={cumulativeCarbonImpact}
                onClose={() => {
                  setLoadedRunInfo(null);
                  setEvaluations([]);
                }}
              />
            )}

            {/* Metrics - shown for both live and historical runs */}
            {(liveMetrics.count > 0 ||
              (queueStatus && queueStatus.total > 0)) && (
              <VStack gap={4} align="stretch">
                <Heading
                  size="sm"
                  color="fg.muted"
                  fontWeight="medium"
                  textTransform="uppercase"
                  letterSpacing="wide"
                >
                  Metrics
                </Heading>
                <LiveMetrics
                  metrics={liveMetrics}
                  queueStatus={loadedRunInfo ? undefined : queueStatus}
                  cumulativeCarbonImpact={cumulativeCarbonImpact}
                />
              </VStack>
            )}

            {/* Document Queue - shows all selected documents and their processing status */}
            {documentQueue.length > 0 && (
              <VStack gap={4} align="stretch">
                <Heading
                  size="sm"
                  color="fg.muted"
                  fontWeight="medium"
                  textTransform="uppercase"
                  letterSpacing="wide"
                >
                  Processing Queue
                </Heading>
                <DocumentQueue documents={documentQueue} />
              </VStack>
            )}

            {/* Ready Queue - shows documents ready to process (before starting) */}
            {documents.length > 0 &&
              documentQueue.length === 0 &&
              evaluations.length === 0 &&
              !loadedRunInfo && (
                <VStack gap={4} align="stretch">
                  <Heading
                    size="sm"
                    color="fg.muted"
                    fontWeight="medium"
                    textTransform="uppercase"
                    letterSpacing="wide"
                  >
                    Ready to Process
                  </Heading>
                  <ReadyQueue
                    documents={documents.map((d) => ({
                      document_id: d.document_id,
                      filename: d.filename,
                    }))}
                    labelCount={groundTruthLabelCount}
                  />
                </VStack>
              )}

            {/* Search and Documents */}
            {evaluations.length > 0 ? (
              <VStack gap={4} align="stretch">
                <Flex align="flex-start" justify="space-between" gap={6}>
                  <Box flex={1}>
                    <Heading
                      size="sm"
                      color="fg.muted"
                      fontWeight="medium"
                      textTransform="uppercase"
                      letterSpacing="wide"
                      mb={1}
                    >
                      Document Evaluations
                    </Heading>
                    <Text fontSize="sm" color="fg.subtle">
                      Showing {filteredEvaluations.length} of{" "}
                      {evaluations.length}{" "}
                      {evaluations.length === 1 ? "document" : "documents"}
                    </Text>
                  </Box>
                  <Box w="96" flexShrink={0}>
                    <SearchBar
                      value={searchQuery}
                      onChange={setSearchQuery}
                      placeholder="Search documents, stages, results..."
                    />
                  </Box>
                </Flex>

                {/* Filters */}
                <FilterPanel
                  filters={filters}
                  onChange={setFilters}
                  totalCount={evaluations.length}
                  filteredCount={filteredEvaluations.length}
                  filteredDocuments={filteredEvaluations}
                  runId={loadedRunInfo?.run_id || currentRunId}
                  metrics={liveMetrics}
                  runInfo={{
                    runId: loadedRunInfo?.run_id || currentRunId,
                    modelName: loadedRunInfo?.model_name || runConfig.modelName,
                    reasoningEffort: runConfig.reasoningEffort || undefined,
                    startTime: loadedRunInfo?.start_time,
                  }}
                />

                {/* Documents List */}
                {filteredEvaluations.length === 0 ? (
                  <EmptyState variant="no-results" searchQuery={searchQuery} />
                ) : (
                  <VStack gap={4} align="stretch">
                    {filteredEvaluations.map((docEval, index) => (
                      <DocumentCard
                        key={docEval.document_id}
                        document={docEval}
                        isExpanded={selectedDocument === docEval.document_id}
                        onToggle={handleToggleDocument}
                        runId={loadedRunInfo?.run_id || currentRunId}
                        onReload={handleReloadCurrentRun}
                      />
                    ))}
                  </VStack>
                )}
              </VStack>
            ) : (
              <GettingStarted
                hasDocuments={!!dataDir}
                hasLabels={groundTruthLabelCount > 0}
              />
            )}
          </VStack>
        ) : viewMode === "history" ? (
          <Box>
            <Suspense fallback={<LoadingSpinner />}>
              <HistoryView
                onLoadRun={handleLoadRun}
                onResumeRun={handleResumeRun}
              />
            </Suspense>
          </Box>
        ) : viewMode === "compare" ? (
          <Box>
            <Suspense fallback={<LoadingSpinner />}>
              <ModelComparisonView onLoadRun={handleLoadRun} />
            </Suspense>
          </Box>
        ) : (
          <Box>
            <Suspense fallback={<LoadingSpinner />}>
              <PromptsView />
            </Suspense>
          </Box>
        )}
      </Container>

      {/* Run Config Modal */}
      <RunConfigModal
        isOpen={showConfigModal}
        onClose={() => setShowConfigModal(false)}
        onSubmit={handleConfigSubmit}
        currentConfig={runConfig}
        availableDocuments={documents}
      />

      {/* Toast Notifications */}
      <Toaster position="top-right" richColors closeButton />
    </Box>
  );
};

export default App;
