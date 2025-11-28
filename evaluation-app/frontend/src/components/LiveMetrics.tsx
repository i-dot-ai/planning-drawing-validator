import React, { memo } from "react";
import {
  Card,
  Box,
  Flex,
  Text,
  Icon,
  HStack,
  Tooltip,
  Separator,
  Portal,
} from "@chakra-ui/react";
import {
  Target,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Loader2,
  Layers,
  Leaf,
  Scale,
  Info,
  MessageSquareText,
  Droplet,
} from "lucide-react";
import { CarbonImpact } from "../types";

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
  truePositive:
    "True Positives (TP): Documents correctly predicted as VALID that were actually VALID",
  trueNegative:
    "True Negatives (TN): Documents correctly predicted as INVALID that were actually INVALID",
  falsePositive:
    "False Positives (FP): Documents incorrectly predicted as VALID that were actually INVALID (Type I error)",
  falseNegative:
    "False Negatives (FN): Documents incorrectly predicted as INVALID that were actually VALID (Type II error)",
  reasoningScore:
    "Reasoning Accuracy measures how well the model's reasoning matches the expected reasoning from ground truth. Uses LLM-as-judge to evaluate semantic similarity (0-100%).",
};

// Memoized metric component to prevent unnecessary re-renders
interface MetricProps {
  label: string;
  value: string | number;
  icon?: any;
  variant?: "default" | "success" | "error";
  tooltip?: string;
}

const Metric = memo(
  ({
    label,
    value,
    icon: IconComponent,
    variant = "default",
    tooltip,
  }: MetricProps) => {
    const colors = {
      default: "fg.emphasis",
      success: "green.600",
      error: "red.600",
    };

    const content = (
      <Flex direction="column" gap={1} minW="fit-content" px={4} py={3}>
        <HStack gap={2} color="fg.muted">
          {IconComponent && <Icon as={IconComponent} boxSize="3.5" />}
          <Text
            fontSize="xs"
            fontWeight="medium"
            textTransform="uppercase"
            letterSpacing="wide"
          >
            {label}
          </Text>
          {tooltip && (
            <Icon as={Info} boxSize="3.5" color="gray.400" cursor="help" />
          )}
        </HStack>
        <Text
          fontSize="2xl"
          fontWeight="semibold"
          lineHeight="tight"
          color={colors[variant]}
          style={{ fontVariantNumeric: "tabular-nums" }}
        >
          {value}
        </Text>
      </Flex>
    );

    if (tooltip) {
      return (
        <Tooltip.Root>
          <Tooltip.Trigger asChild>{content}</Tooltip.Trigger>
          <Portal>
            <Tooltip.Positioner>
              <Tooltip.Content
                bg="gray.800"
                color="white"
                px={3}
                py={2}
                borderRadius="md"
                fontSize="xs"
                maxW="280px"
              >
                {tooltip}
              </Tooltip.Content>
            </Tooltip.Positioner>
          </Portal>
        </Tooltip.Root>
      );
    }

    return content;
  },
);

Metric.displayName = "Metric";

interface LiveMetricsProps {
  metrics: {
    tp: number;
    tn: number;
    fp: number;
    fn: number;
    precision: number | null;
    recall: number | null;
    f1Score: number | null;
    accuracy: number | null;
    avgTime: number | null;
    count: number;
    groundTruthCount: number;
    validCount: number;
    invalidCount: number;
    hasGroundTruth: boolean;
    avgClassificationTime: number | null;
    avgValidationTime: number | null;
    avgReasoningScore: number | null;
    reasoningEvaluatedCount: number;
    hasReasoningEvaluation: boolean;
  };
  queueStatus?: {
    queued: number;
    processing: number;
    completed: number;
    total: number;
  };
  cumulativeCarbonImpact?: CarbonImpact | null;
}

export const LiveMetrics = memo<LiveMetricsProps>(
  function LiveMetrics({
    metrics,
    queueStatus,
    cumulativeCarbonImpact,
  }: LiveMetricsProps) {
    const hasQueueInfo = queueStatus && queueStatus.total > 0;

    // Show the component if we have either metrics or queue info
    if (metrics.count === 0 && !hasQueueInfo) {
      return null;
    }

    // Use accuracy from metrics (properly calculated with groundTruthCount denominator)
    const accuracyPercent =
      metrics.accuracy !== null ? metrics.accuracy * 100 : null;

    // Format number with appropriate precision
    const formatNumber = (value: number, decimals: number = 3): string => {
      if (value < 0.000001) {
        return value.toExponential(2);
      }
      return value.toFixed(decimals);
    };

    // Format range with units
    const formatRange = (
      min: number,
      max: number,
      unit: string,
      decimals: number = 3,
    ): string => {
      return `${formatNumber(min, decimals)}-${formatNumber(max, decimals)} ${unit}`;
    };

    return (
      <Card.Root variant="outline">
        <Card.Body p={0}>
          <Box>
            {/* Queue Status Section */}
            {hasQueueInfo && (
              <Box>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, 1fr)",
                  }}
                >
                  <Metric
                    label="Total"
                    value={queueStatus.total}
                    icon={Layers}
                    variant="default"
                  />
                  <Metric
                    label="Queued"
                    value={queueStatus.queued}
                    icon={Clock}
                    variant="default"
                  />
                  <Metric
                    label="Processing"
                    value={queueStatus.processing}
                    icon={Loader2}
                    variant="default"
                  />
                  <Metric
                    label="Completed"
                    value={queueStatus.completed}
                    icon={CheckCircle2}
                    variant="success"
                  />
                </div>
                {metrics.count > 0 && <Separator />}
              </Box>
            )}

            {/* Evaluation Metrics Section */}
            {metrics.count > 0 && (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
                }}
              >
                <Metric
                  label="Documents"
                  value={metrics.count}
                  icon={FileText}
                  variant="default"
                />

                {/* Show evaluation metrics only when ground truth is available */}
                {metrics.hasGroundTruth ? (
                  <>
                    <Metric
                      label="Accuracy"
                      value={
                        accuracyPercent !== null
                          ? `${accuracyPercent.toFixed(0)}%`
                          : "—"
                      }
                      icon={Target}
                      variant="default"
                      tooltip={METRIC_EXPLANATIONS.accuracy}
                    />
                    <Metric
                      label="Precision"
                      value={
                        metrics.precision !== null
                          ? `${(metrics.precision * 100).toFixed(0)}%`
                          : "—"
                      }
                      icon={TrendingUp}
                      variant="default"
                      tooltip={METRIC_EXPLANATIONS.precision}
                    />
                    <Metric
                      label="Recall"
                      value={
                        metrics.recall !== null
                          ? `${(metrics.recall * 100).toFixed(0)}%`
                          : "—"
                      }
                      icon={TrendingUp}
                      variant="default"
                      tooltip={METRIC_EXPLANATIONS.recall}
                    />
                    <Metric
                      label="F1 Score"
                      value={
                        metrics.f1Score !== null
                          ? `${(metrics.f1Score * 100).toFixed(0)}%`
                          : "—"
                      }
                      icon={Scale}
                      variant="default"
                      tooltip={METRIC_EXPLANATIONS.f1Score}
                    />
                    {metrics.hasReasoningEvaluation && (
                      <Metric
                        label="Reasoning"
                        value={
                          metrics.avgReasoningScore !== null
                            ? `${(metrics.avgReasoningScore * 100).toFixed(0)}%`
                            : "—"
                        }
                        icon={MessageSquareText}
                        variant="default"
                        tooltip={METRIC_EXPLANATIONS.reasoningScore}
                      />
                    )}
                  </>
                ) : (
                  <>
                    {/* Show predicted counts when no ground truth */}
                    <Metric
                      label="Valid"
                      value={metrics.validCount}
                      icon={ThumbsUp}
                      variant="success"
                    />
                    <Metric
                      label="Invalid"
                      value={metrics.invalidCount}
                      icon={ThumbsDown}
                      variant="error"
                    />
                  </>
                )}

                <Metric
                  label="Avg Time"
                  value={
                    metrics.avgTime !== null
                      ? `${metrics.avgTime.toFixed(1)}s`
                      : "—"
                  }
                  icon={Clock}
                  variant="default"
                />
              </div>
            )}

            {/* Detailed Metrics Section */}
            {(metrics.hasGroundTruth ||
              metrics.avgClassificationTime !== null ||
              metrics.avgValidationTime !== null) && (
              <Box>
                <Separator />
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
                  }}
                >
                  {metrics.hasGroundTruth && (
                    <>
                      <Metric
                        label="True Positive"
                        value={metrics.tp}
                        icon={CheckCircle2}
                        variant="success"
                        tooltip={METRIC_EXPLANATIONS.truePositive}
                      />
                      <Metric
                        label="True Negative"
                        value={metrics.tn}
                        icon={CheckCircle2}
                        variant="success"
                        tooltip={METRIC_EXPLANATIONS.trueNegative}
                      />
                      <Metric
                        label="False Positive"
                        value={metrics.fp}
                        icon={XCircle}
                        variant="error"
                        tooltip={METRIC_EXPLANATIONS.falsePositive}
                      />
                      <Metric
                        label="False Negative"
                        value={metrics.fn}
                        icon={XCircle}
                        variant="error"
                        tooltip={METRIC_EXPLANATIONS.falseNegative}
                      />
                    </>
                  )}

                  {metrics.avgClassificationTime !== null && (
                    <Metric
                      label="Classification"
                      value={`${metrics.avgClassificationTime.toFixed(1)}s`}
                      icon={Clock}
                      variant="default"
                    />
                  )}
                  {metrics.avgValidationTime !== null && (
                    <Metric
                      label="Validation"
                      value={`${metrics.avgValidationTime.toFixed(1)}s`}
                      icon={Clock}
                      variant="default"
                    />
                  )}
                </div>
              </Box>
            )}

            {/* Environmental Impact Section */}
            {cumulativeCarbonImpact && metrics.count > 0 && (
              <Box>
                <Separator />
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3, 1fr)",
                  }}
                >
                  <Metric
                    label="CO₂ Equivalent"
                    value={formatRange(
                      cumulativeCarbonImpact.gwp_kgco2eq_min,
                      cumulativeCarbonImpact.gwp_kgco2eq_max,
                      "kg",
                      3,
                    )}
                    icon={Leaf}
                    variant="default"
                  />
                  <Metric
                    label="Energy"
                    value={formatRange(
                      cumulativeCarbonImpact.energy_kwh_min,
                      cumulativeCarbonImpact.energy_kwh_max,
                      "kWh",
                      3,
                    )}
                    icon={Leaf}
                    variant="default"
                  />
                  <Metric
                    label="Water"
                    value={formatRange(
                      cumulativeCarbonImpact.wcf_l_min,
                      cumulativeCarbonImpact.wcf_l_max,
                      "L",
                      3,
                    )}
                    icon={Droplet}
                    variant="default"
                  />
                </div>
              </Box>
            )}
          </Box>
        </Card.Body>
      </Card.Root>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison: only re-render if metrics values actually changed
    const metricsEqual =
      prevProps.metrics.count === nextProps.metrics.count &&
      prevProps.metrics.tp === nextProps.metrics.tp &&
      prevProps.metrics.tn === nextProps.metrics.tn &&
      prevProps.metrics.fp === nextProps.metrics.fp &&
      prevProps.metrics.fn === nextProps.metrics.fn &&
      prevProps.metrics.precision === nextProps.metrics.precision &&
      prevProps.metrics.recall === nextProps.metrics.recall &&
      prevProps.metrics.f1Score === nextProps.metrics.f1Score &&
      prevProps.metrics.accuracy === nextProps.metrics.accuracy &&
      prevProps.metrics.avgTime === nextProps.metrics.avgTime &&
      prevProps.metrics.validCount === nextProps.metrics.validCount &&
      prevProps.metrics.invalidCount === nextProps.metrics.invalidCount &&
      prevProps.metrics.hasGroundTruth === nextProps.metrics.hasGroundTruth;

    const queueEqual =
      (!prevProps.queueStatus && !nextProps.queueStatus) ||
      (prevProps.queueStatus &&
        nextProps.queueStatus &&
        prevProps.queueStatus.queued === nextProps.queueStatus.queued &&
        prevProps.queueStatus.processing === nextProps.queueStatus.processing &&
        prevProps.queueStatus.completed === nextProps.queueStatus.completed &&
        prevProps.queueStatus.total === nextProps.queueStatus.total);

    const carbonEqual =
      (!prevProps.cumulativeCarbonImpact &&
        !nextProps.cumulativeCarbonImpact) ||
      (!!prevProps.cumulativeCarbonImpact &&
        !!nextProps.cumulativeCarbonImpact &&
        prevProps.cumulativeCarbonImpact.gwp_kgco2eq_min ===
          nextProps.cumulativeCarbonImpact.gwp_kgco2eq_min &&
        prevProps.cumulativeCarbonImpact.gwp_kgco2eq_max ===
          nextProps.cumulativeCarbonImpact.gwp_kgco2eq_max &&
        prevProps.cumulativeCarbonImpact.wcf_l_min ===
          nextProps.cumulativeCarbonImpact.wcf_l_min &&
        prevProps.cumulativeCarbonImpact.wcf_l_max ===
          nextProps.cumulativeCarbonImpact.wcf_l_max);

    return !!(metricsEqual && queueEqual && carbonEqual);
  },
);
