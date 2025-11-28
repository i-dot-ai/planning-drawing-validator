import { useMemo } from "react";
import { DocumentEvaluation } from "../types";

/**
 * Live metrics calculated from evaluation results
 */
export interface LiveMetrics {
  // Confusion matrix
  tp: number;
  tn: number;
  fp: number;
  fn: number;

  // Performance metrics
  precision: number | null;
  recall: number | null;
  f1Score: number | null;
  accuracy: number | null;
  avgTime: number | null;

  // Counts
  count: number;
  groundTruthCount: number;
  validCount: number;
  invalidCount: number;
  hasGroundTruth: boolean;

  // Stage timing
  avgClassificationTime: number | null;
  avgValidationTime: number | null;

  // Reasoning evaluation metrics
  avgReasoningScore: number | null;
  reasoningEvaluatedCount: number;
  hasReasoningEvaluation: boolean;
}

/**
 * Custom hook to calculate live metrics from evaluation results
 *
 * Efficiently calculates confusion matrix, performance metrics, and timing statistics
 * from document evaluations, with automatic detection of ground truth availability.
 *
 * @param evaluations - Array of document evaluations
 * @returns Calculated metrics object
 */
export function useMetrics(evaluations: DocumentEvaluation[]): LiveMetrics {
  return useMemo(() => {
    const completed = evaluations.filter((e) => e.final_result);

    let tp = 0,
      tn = 0,
      fp = 0,
      fn = 0;
    let totalTime = 0,
      timeCount = 0;
    let validCount = 0,
      invalidCount = 0;

    // Stage timing accumulators
    let classificationTime = 0,
      validationTime = 0;
    let classificationCount = 0,
      validationCount = 0;

    // Reasoning evaluation accumulators
    let totalReasoningScore = 0,
      reasoningEvaluatedCount = 0;

    // Check if we have ground truth (expected_validity is meaningful)
    const hasGroundTruth = completed.some((e) => {
      const validity = (e.expected_validity || "").toUpperCase();
      return validity && validity !== "UNKNOWN";
    });

    for (const e of completed) {
      const gt = (e.expected_validity || "").toUpperCase();
      const pr = (e.final_result!.predicted_validity || "").toUpperCase();

      // Count predicted results
      if (pr === "VALID") validCount++;
      else if (pr === "INVALID") invalidCount++;

      // Only compute confusion matrix if ground truth exists
      if (hasGroundTruth) {
        if (gt === "VALID" && pr === "VALID") tp++;
        else if (gt === "INVALID" && pr === "INVALID") tn++;
        else if (gt === "INVALID" && pr === "VALID") fp++;
        else if (gt === "VALID" && pr === "INVALID") fn++;
      }

      // Accumulate total execution time
      const t = e.final_result!.execution_time;
      if (typeof t === "number" && !Number.isNaN(t)) {
        totalTime += t;
        timeCount++;
      }

      // Accumulate stage-level timing
      if (e.stages) {
        for (const stage of e.stages) {
          const stageTime = stage.execution_time;
          if (typeof stageTime === "number" && !Number.isNaN(stageTime)) {
            if (stage.stage === "classification") {
              classificationTime += stageTime;
              classificationCount++;
            } else if (stage.stage === "validation") {
              validationTime += stageTime;
              validationCount++;
            }
          }
        }
      }

      // Accumulate reasoning evaluation score
      const reasoningScore = e.final_result?.reasoning_match_score;
      if (
        e.final_result?.reasoning_evaluated &&
        typeof reasoningScore === "number" &&
        !Number.isNaN(reasoningScore)
      ) {
        totalReasoningScore += reasoningScore;
        reasoningEvaluatedCount++;
      }
    }

    // Calculate derived metrics
    const precision = tp + fp > 0 ? tp / (tp + fp) : null;
    const recall = tp + fn > 0 ? tp / (tp + fn) : null;
    // F1 Score: harmonic mean of precision and recall
    const f1Score =
      precision !== null && recall !== null && precision + recall > 0
        ? (2 * precision * recall) / (precision + recall)
        : null;
    // Accuracy: (TP + TN) / total documents with ground truth
    const groundTruthCount = tp + tn + fp + fn;
    const accuracy = groundTruthCount > 0 ? (tp + tn) / groundTruthCount : null;
    const avgTime = timeCount > 0 ? totalTime / timeCount : null;
    const avgClassificationTime =
      classificationCount > 0 ? classificationTime / classificationCount : null;
    const avgValidationTime =
      validationCount > 0 ? validationTime / validationCount : null;
    const avgReasoningScore =
      reasoningEvaluatedCount > 0
        ? totalReasoningScore / reasoningEvaluatedCount
        : null;
    const hasReasoningEvaluation = reasoningEvaluatedCount > 0;

    return {
      tp,
      tn,
      fp,
      fn,
      precision,
      recall,
      f1Score,
      accuracy,
      avgTime,
      count: completed.length,
      groundTruthCount,
      validCount,
      invalidCount,
      hasGroundTruth,
      avgClassificationTime,
      avgValidationTime,
      avgReasoningScore,
      reasoningEvaluatedCount,
      hasReasoningEvaluation,
    };
  }, [evaluations]);
}
