import { useState, useCallback, useRef, startTransition } from "react";
import { DocumentEvaluation, WebSocketMessage } from "../types";
import { useMetrics } from "./useMetrics";
import { useDocumentQueue } from "./useDocumentQueue";
import { WS_MESSAGE_TYPES, EVALUATION_STAGES } from "../lib/constants";
import { api } from "../lib/api";

export function useEvaluation() {
  const [evaluations, setEvaluations] = useState<DocumentEvaluation[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [activeDocumentId, setActiveDocumentId] = useState<string>("");
  const [currentRunId, setCurrentRunId] = useState<string>("");
  const [queueStatus, setQueueStatus] = useState<{
    queued: number;
    processing: number;
    completed: number;
    total: number;
  }>({ queued: 0, processing: 0, completed: 0, total: 0 });
  const hasLoadedRef = useRef(false);

  // Use the new hooks
  const queue = useDocumentQueue();
  const liveMetrics = useMetrics(evaluations);

  const handleWebSocketMessage = useCallback(
    (message: WebSocketMessage) => {
      const { type, data } = message;

      switch (type) {
        case WS_MESSAGE_TYPES.EVALUATION_STARTED:
          setIsRunning(true);
          setEvaluations([]);
          setActiveDocumentId("");

          // Initialize queue with all documents from the start message
          if (
            (data as any).documents &&
            Array.isArray((data as any).documents)
          ) {
            queue.initializeQueue((data as any).documents);
          }

          // Initialize queue status
          if ((data as any).total_documents !== undefined) {
            setQueueStatus({
              queued: (data as any).queued || (data as any).total_documents,
              processing: (data as any).processing || 0,
              completed: (data as any).completed || 0,
              total: (data as any).total_documents,
            });
          }

          if ((data as any).run_id) {
            setCurrentRunId((data as any).run_id);
          }
          break;

        case WS_MESSAGE_TYPES.DOCUMENT_STARTED:
          startTransition(() => {
            // Mark document as processing in queue
            queue.markAsProcessing(
              (data as any).document_id,
              (data as any).filename,
            );

            setEvaluations((prev) => {
              const existing = prev.find(
                (doc) => doc.document_id === (data as any).document_id,
              );
              if (existing) return prev;

              return [
                ...prev,
                {
                  document_id: (data as any).document_id,
                  filename: (data as any).filename,
                  expected_validity:
                    (data as any).expected_validity || "Unknown",
                  status: "running",
                  stages: [
                    {
                      stage: EVALUATION_STAGES.CLASSIFICATION.id,
                      stage_name: EVALUATION_STAGES.CLASSIFICATION.name,
                      status: "pending",
                    },
                    {
                      stage: EVALUATION_STAGES.VALIDATION.id,
                      stage_name: EVALUATION_STAGES.VALIDATION.name,
                      status: "pending",
                    },
                  ],
                },
              ];
            });
            setActiveDocumentId((data as any).document_id);
          });
          break;

        case WS_MESSAGE_TYPES.STAGE_STARTED:
          startTransition(() => {
            setEvaluations((prev) => {
              const docIndex = prev.findIndex(
                (doc) => doc.document_id === (data as any).document_id,
              );
              if (docIndex === -1) return prev;

              const doc = prev[docIndex];
              const stageIndex = doc.stages.findIndex(
                (stage) => stage.stage === (data as any).stage,
              );
              if (stageIndex === -1) return prev;

              const stage = doc.stages[stageIndex];
              // Check if stage is already running
              if (stage.status === "running") {
                return prev; // No change needed
              }

              const updated = [...prev];
              updated[docIndex] = {
                ...doc,
                stages: [
                  ...doc.stages.slice(0, stageIndex),
                  {
                    ...stage,
                    status: "running" as const,
                    prompt: (data as any).prompt,
                  },
                  ...doc.stages.slice(stageIndex + 1),
                ],
              };
              return updated;
            });
            setActiveDocumentId((data as any).document_id);
          });
          break;

        case WS_MESSAGE_TYPES.STAGE_COMPLETED:
          startTransition(() => {
            setEvaluations((prev) => {
              // Find the document that needs updating
              const docIndex = prev.findIndex(
                (doc) => doc.document_id === (data as any).document_id,
              );
              if (docIndex === -1) return prev; // Document not found, no change

              const doc = prev[docIndex];
              const stageIndex = doc.stages.findIndex(
                (stage) => stage.stage === (data as any).stage,
              );
              if (stageIndex === -1) return prev; // Stage not found, no change

              const stage = doc.stages[stageIndex];
              // Check if stage is already completed with same data
              if (
                stage.status === "completed" &&
                stage.model_output === (data as any).model_output
              ) {
                return prev; // No change needed
              }

              // Create updated array only if data actually changed
              const updated = [...prev];
              updated[docIndex] = {
                ...doc,
                stages: [
                  ...doc.stages.slice(0, stageIndex),
                  {
                    ...stage,
                    status: "completed" as const,
                    prompt: (data as any).prompt || stage.prompt,
                    model_output: (data as any).model_output,
                    reasoning: (data as any).reasoning,
                    confidence: (data as any).confidence,
                    json_data: (data as any).json_data,
                    execution_time: (data as any).execution_time,
                  },
                  ...doc.stages.slice(stageIndex + 1),
                ],
              };
              return updated;
            });
          });
          break;

        case WS_MESSAGE_TYPES.DOCUMENT_COMPLETED:
          startTransition(() => {
            // Remove completed document from queue
            queue.markAsCompleted((data as any).document_id);

            setEvaluations((prev) => {
              const docIndex = prev.findIndex(
                (doc) => doc.document_id === (data as any).document_id,
              );
              if (docIndex === -1) return prev; // Document not found

              const doc = prev[docIndex];
              // Check if already completed with same result
              if (
                doc.status === "completed" &&
                doc.final_result === (data as any).result
              ) {
                return prev; // No change needed
              }

              // Create updated array only if data changed
              const updated = [...prev];
              updated[docIndex] = {
                ...doc,
                status: "completed",
                final_result: (data as any).result,
                stages: doc.stages.map((stage) => ({
                  ...stage,
                  status: "completed",
                })),
              };
              return updated;
            });
          });
          break;

        case WS_MESSAGE_TYPES.DOCUMENT_ERROR:
          startTransition(() => {
            // Mark document as error in queue
            queue.markAsError((data as any).document_id);

            setEvaluations((prev) => {
              const docIndex = prev.findIndex(
                (doc) => doc.document_id === (data as any).document_id,
              );
              if (docIndex === -1) return prev;

              const doc = prev[docIndex];
              // Check if already in error state
              if (doc.status === "error") {
                return prev; // No change needed
              }

              const updated = [...prev];
              updated[docIndex] = { ...doc, status: "error" };
              return updated;
            });
          });
          break;

        case WS_MESSAGE_TYPES.QUEUE_STATUS:
          startTransition(() => {
            setQueueStatus((prev) => {
              const newStatus = {
                queued: (data as any).queued || 0,
                processing: (data as any).processing || 0,
                completed: (data as any).completed || 0,
                total: (data as any).total || 0,
              };

              // Only update if values actually changed
              if (
                prev.queued === newStatus.queued &&
                prev.processing === newStatus.processing &&
                prev.completed === newStatus.completed &&
                prev.total === newStatus.total
              ) {
                return prev; // No change, return same object reference
              }

              return newStatus;
            });
          });
          break;

        case WS_MESSAGE_TYPES.EVALUATION_COMPLETED:
          startTransition(() => {
            setIsRunning(false);
            queue.clearQueue();
            setQueueStatus({
              queued: 0,
              processing: 0,
              completed: 0,
              total: 0,
            });
          });
          break;

        case WS_MESSAGE_TYPES.EVALUATION_STOPPED:
          startTransition(() => {
            setIsRunning(false);
            queue.clearQueue();
            setQueueStatus({
              queued: 0,
              processing: 0,
              completed: 0,
              total: 0,
            });
          });
          break;
      }
    },
    [
      queue.initializeQueue,
      queue.markAsProcessing,
      queue.markAsCompleted,
      queue.markAsError,
      queue.clearQueue,
    ],
  );

  const loadMostRecentRun = useCallback(async () => {
    if (hasLoadedRef.current) {
      return;
    }

    hasLoadedRef.current = true; // Set immediately to prevent double-loading

    try {
      // Check if there's a currently running evaluation first
      const statusData = await api.evaluation.getStatus();

      if (statusData.status === "running") {
        // Load current running evaluation progress
        const currentRun = await api.evaluation.getCurrentRun();
        const completedDocs = (currentRun.documents || []).map((doc: any) => {
          const stages = doc.stages
            ? doc.stages.map((stage: any) => ({
                ...stage,
                status: stage.status || ("completed" as const),
              }))
            : [
                {
                  stage: EVALUATION_STAGES.CLASSIFICATION.id,
                  stage_name: EVALUATION_STAGES.CLASSIFICATION.name,
                  status: "completed" as const,
                },
                {
                  stage: EVALUATION_STAGES.VALIDATION.id,
                  stage_name: EVALUATION_STAGES.VALIDATION.name,
                  status: "completed" as const,
                },
              ];

          return {
            document_id: doc.document_id,
            filename: doc.filename,
            expected_validity: doc.expected_validity || "Unknown",
            status: "completed" as const,
            stages,
            final_result: {
              predicted_validity: doc.predicted_validity,
              predicted_reasoning: doc.predicted_reasoning,
              confidence: doc.confidence,
              correct: doc.is_correct,
              prompt_type: doc.prompt_type,
              execution_time: doc.execution_time,
              reasoning_match_score: doc.reasoning_match_score,
              reasoning_evaluated: doc.reasoning_evaluated,
              reasoning_explanation: doc.reasoning_explanation,
            },
          };
        });
        setEvaluations(completedDocs);
        setIsRunning(true);
        return;
      }

      // No running evaluation, try to load most recent run (prefer completed over running)
      const runsData = await api.runs.getRuns();
      const runs = runsData.runs || [];

      // Find most recent completed run first, or fall back to most recent run
      let targetRun = runs.find((r: any) => r.status === "completed");
      if (!targetRun && runs.length > 0) {
        // No completed runs, use the most recent one (first in list)
        targetRun = runs[0];
      }

      if (!targetRun) {
        return;
      }

      // Get full run details with reconstructed stage data
      const runData = await api.runs.getRun(targetRun.run_id);

      // Map documents with full stage information
      const completedDocs = (runData.documents || []).map((doc: any) => {
        // Ensure stages have status field set to completed
        const stages = doc.stages
          ? doc.stages.map((stage: any) => ({
              ...stage,
              status: stage.status || ("completed" as const),
            }))
          : [
              {
                stage: EVALUATION_STAGES.CLASSIFICATION.id,
                stage_name: EVALUATION_STAGES.CLASSIFICATION.name,
                status: "completed" as const,
              },
              {
                stage: EVALUATION_STAGES.VALIDATION.id,
                stage_name: EVALUATION_STAGES.VALIDATION.name,
                status: "completed" as const,
              },
            ];

        return {
          document_id: doc.document_id,
          filename: doc.filename,
          expected_validity: doc.expected_validity || "Unknown",
          status: "completed" as const,
          stages,
          final_result: {
            predicted_validity: doc.predicted_validity,
            predicted_reasoning: doc.predicted_reasoning,
            confidence: doc.confidence,
            correct: doc.is_correct,
            prompt_type: doc.prompt_type,
            execution_time: doc.execution_time,
            reasoning_match_score: doc.reasoning_match_score,
            reasoning_evaluated: doc.reasoning_evaluated,
            reasoning_explanation: doc.reasoning_explanation,
          },
        };
      });

      setEvaluations(completedDocs);
    } catch {
      // Silently ignore load errors
    }
  }, []);

  return {
    evaluations,
    setEvaluations,
    isRunning,
    setIsRunning,
    activeDocumentId,
    setActiveDocumentId,
    currentRunId,
    documentQueue: queue.documentQueue,
    queueStatus,
    handleWebSocketMessage,
    liveMetrics,
    loadMostRecentRun,
  };
}
