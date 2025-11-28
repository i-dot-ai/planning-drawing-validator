/**
 * Type Definitions for Planning Drawing Validation
 *
 * Following the principle: Explicit Over Implicit
 * All types are well-documented with clear purpose.
 */

/**
 * Upload status for tracking validation progress
 */
export type UploadStatusType =
  | "uploading"
  | "validating"
  | "complete"
  | "error";

/**
 * Individual requirement check result
 */
export interface Requirement {
  /** The requirement being checked (e.g., "Must include scale 1:50 or 1:100") */
  requirement: string;
  /** Check result: PASS, FAIL, or NEEDS_REVIEW */
  status: string;
  /** Optional detailed explanation of the check result */
  details?: string | null;
}

/**
 * Individual drawing within a mixed drawing file
 *
 * Mixed drawings contain multiple types (e.g., floor plan + elevations in one PDF).
 * Each constituent drawing is validated separately.
 */
export interface IndividualDrawing {
  /** Type of this drawing (FLOOR_PLAN, ELEVATION, etc.) */
  drawing_type: string;
  /** Overall validity: VALID, INVALID, or CLARIFICATION_NEEDED */
  validity: string;
  /** AI-generated explanation of the validity decision */
  reasoning: string;
  /** Confidence level: HIGH, MEDIUM, or LOW */
  confidence: string;
  /** List of requirements checked for this drawing */
  requirements_checked: Requirement[];
}

/**
 * Complete validation result from the API
 */
export interface ValidationResult {
  /** Unique identifier for this validation run */
  document_id: string;
  /** Classified document type (FLOOR_PLAN, SITE_PLAN, etc.) */
  document_type: string;
  /** Overall validity: VALID, INVALID, or CLARIFICATION_NEEDED */
  validity: string;
  /** AI-generated explanation of the validation outcome */
  reasoning: string;
  /** Confidence in the classification: HIGH, MEDIUM, or LOW */
  confidence: string;
  /** List of planning requirements that were checked */
  requirements_checked: Requirement[];
  /** Time taken to process validation (in seconds) */
  execution_time: number;
  /** Whether validation completed successfully */
  success: boolean;
  /** Error message if validation failed */
  error_message?: string | null;
  /** Type of prompt used for validation */
  prompt_type?: string | null;
  /** Whether this file contains multiple drawing types */
  is_mixed_drawing: boolean;
  /** Individual drawings if this is a mixed drawing */
  constituent_drawings?: IndividualDrawing[];
  /** Gemini's extended thinking from classification stage (optional) */
  classification_thinking?: string | null;
  /** Gemini's extended thinking from validation stage (optional) */
  validation_thinking?: string | null;
}

/**
 * Upload status tracking
 */
export interface UploadStatus {
  /** Current upload state */
  status: UploadStatusType;
  /** Progress from 0 to 1 (optional, calculated from status if not provided) */
  progress?: number;
  /** Status message for display */
  message?: string;
}

/**
 * Complete document upload with file, status, and results
 */
export interface DocumentUpload {
  /** Unique identifier for this upload */
  id: string;
  /** The uploaded file */
  file: File;
  /** Current status of validation */
  status: UploadStatus;
  /** Validation result once complete */
  result?: ValidationResult;
}
