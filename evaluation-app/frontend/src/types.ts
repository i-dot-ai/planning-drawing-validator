export interface DocumentInfo {
  document_id: string;
  filename: string;
  validity: string;
  reason: string;
}

export interface ModelInfo {
  id: string;
  display_name: string;
  is_default: boolean;
  provider?: string | null;
  reasoning_effort?: string | null; // "none", "low", "medium", "high"
}

export interface JSONData {
  [key: string]: string | number | boolean | null | JSONData | JSONData[];
}

export interface ConstituentValidation {
  drawing_type: string;
  description: string;
  location: string;
  validation: {
    validity_assessment: string;
    overall_confidence: string;
    assessment_reasoning: string;
    validation_checks: JSONData;
  };
}

export interface EvaluationStage {
  stage: string; // Stage identifier: "classification" or "validation"
  stage_name: string;
  status: "pending" | "running" | "completed" | "error";
  prompt?: string;
  model_output?: string;
  reasoning?: string;
  confidence?: string;
  json_data?: JSONData;
  error?: string;
  execution_time?: number;
  is_composite?: boolean;
  constituent_validations?: ConstituentValidation[];
}

export interface DocumentEvaluation {
  document_id: string;
  filename: string;
  expected_validity: string;
  status: "pending" | "running" | "completed" | "error";
  stages: EvaluationStage[];
  final_result?: {
    predicted_validity: string;
    predicted_reasoning: string;
    confidence: string;
    correct: boolean;
    prompt_type: string;
    execution_time: number;
    carbon_impact?: CarbonImpact;
    // Reasoning evaluation fields
    reasoning_match_score?: number | null;
    reasoning_evaluated?: boolean;
    reasoning_explanation?: string | null;
  };
}

export interface CarbonImpact {
  energy_kwh_min: number;
  energy_kwh_max: number;
  gwp_kgco2eq_min: number;
  gwp_kgco2eq_max: number;
  adpe_kgsbeq_min: number;
  adpe_kgsbeq_max: number;
  pe_mj_min: number;
  pe_mj_max: number;
  wcf_l_min: number;
  wcf_l_max: number;
}

export interface RunDocument {
  document_id: string;
  filename: string;
  expected_validity?: string;
  predicted_validity?: string;
  predicted_reasoning?: string;
  confidence?: number;
  correct?: boolean;
  is_correct?: boolean;
  prompt_type?: string;
  execution_time?: number;
  stages?: EvaluationStage[];
  carbon_impact?: CarbonImpact;
  // Reasoning evaluation fields
  reasoning_match_score?: number | null;
  reasoning_evaluated?: boolean;
  reasoning_explanation?: string | null;
  expected_reasoning?: string | null;
}

export interface EvaluationRun {
  run_id: string;
  name?: string;
  run_name?: string;
  timestamp: string;
  start_time?: string;
  total_documents: number;
  completed_documents: number;
  overall_accuracy?: number;
  accuracy?: number;
  execution_time?: number;
  status: string;
  document_count: number;
  documents?: RunDocument[];
  model_name?: string;
  reasoning_effort?: string | null; // "none", "low", "medium", "high"
}

export interface WebSocketMessage<T = unknown> {
  type: string;
  data: T;
}

export interface PreviewInfo {
  mediaType: string;
  url: string;
}

export interface PromptVersion {
  version_id: string;
  version_number: number;
  timestamp: string;
  author: string;
  description: string;
  is_active: boolean;
  parent_version_id: string | null;
  content: string;
  metadata: Record<string, any>;
}

export interface PromptSummary {
  name: string;
  type: "classification" | "validation";
  file_path: string;
  version_count: number;
  active_version_id: string | null;
  last_updated: string | null;
  last_author: string | null;
}

export interface PromptDetails {
  name: string;
  type: "classification" | "validation";
  current_content: string;
  versions: PromptVersion[];
  active_version: {
    version_id: string;
    timestamp: string;
    author: string;
    description: string;
  } | null;
}

export interface ModelStats {
  model_name: string;
  reasoning_effort: string | null; // "none", "low", "medium", "high" - only set when grouping by effort
  run_count: number;
  avg_accuracy: number | null;
  min_accuracy: number | null;
  max_accuracy: number | null;
  std_accuracy: number | null;
  avg_execution_time: number | null;
  total_documents: number;
  avg_precision: number | null;
  avg_recall: number | null;
  avg_f1_score: number | null;
  avg_reasoning_accuracy: number | null; // Average of reasoning_match_score where evaluated
  reasoning_eval_count: number; // Number of documents with reasoning evaluation
  latest_run_timestamp: string;
  run_ids: string[];
}
