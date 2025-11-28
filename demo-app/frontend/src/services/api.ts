/**
 * API Service for Planning Drawing Validation
 *
 * Handles all communication with the FastAPI backend.
 * Following the principle: Explicit Over Implicit
 */

import axios, { AxiosError } from "axios";
import type { ValidationResult } from "../types";

/**
 * API configuration constants
 */
const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || "/api",
  VALIDATION_TIMEOUT_MS: 300_000, // 5 minutes for document processing
  HEALTH_CHECK_TIMEOUT_MS: 5_000, // 5 seconds for health check
} as const;

/**
 * API endpoints
 */
const ENDPOINTS = {
  VALIDATE: "/validate",
  HEALTH: "/health",
} as const;

/**
 * Upload and validate a planning document
 *
 * Sends the file to the backend for AI-powered classification and validation.
 *
 * @param file - The planning drawing file to validate
 * @returns Validation result with classification, requirements, and reasoning
 * @throws Error if validation fails or request times out
 */
export async function validateDocument(file: File): Promise<ValidationResult> {
  const formData = buildFormDataWithFile(file);

  try {
    const response = await axios.post<ValidationResult>(
      `${API_CONFIG.BASE_URL}${ENDPOINTS.VALIDATE}`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: API_CONFIG.VALIDATION_TIMEOUT_MS,
      },
    );

    return response.data;
  } catch (error) {
    throw createValidationError(error);
  }
}

/**
 * Check if the API backend is healthy and reachable
 *
 * @returns true if API is healthy, false otherwise
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const healthUrl = buildHealthCheckUrl();
    const response = await axios.get(healthUrl, {
      timeout: API_CONFIG.HEALTH_CHECK_TIMEOUT_MS,
    });

    return response.data.status === "healthy";
  } catch {
    return false;
  }
}

/**
 * Build FormData object with the file attached
 *
 * @param file - File to attach
 * @returns FormData ready for multipart upload
 */
function buildFormDataWithFile(file: File): FormData {
  const formData = new FormData();
  formData.append("file", file);
  return formData;
}

/**
 * Build health check URL from base API URL
 *
 * Handles the case where API_BASE_URL includes '/api' suffix.
 *
 * @returns Complete health check URL
 */
function buildHealthCheckUrl(): string {
  const baseWithoutApi = API_CONFIG.BASE_URL.replace("/api", "");
  return `${baseWithoutApi}${ENDPOINTS.HEALTH}`;
}

/**
 * Create a user-friendly error from an API error response
 *
 * Extracts the most relevant error message from axios error.
 *
 * @param error - Error from axios request
 * @returns Error with descriptive message
 */
function createValidationError(error: unknown): Error {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string }>;
    const errorDetail = axiosError.response?.data?.detail;
    const errorMessage = errorDetail || axiosError.message;

    return new Error(`Validation failed: ${errorMessage}`);
  }

  // For non-axios errors, preserve original error
  if (error instanceof Error) {
    return error;
  }

  // Fallback for unknown error types
  return new Error("Validation failed: An unexpected error occurred");
}
