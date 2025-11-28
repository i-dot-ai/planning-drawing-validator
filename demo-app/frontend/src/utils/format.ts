import { CheckCircle2, XCircle, Loader2, LucideIcon } from "lucide-react";

/**
 * Format file size in bytes to human-readable string
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * Format document type from SNAKE_CASE to Title Case
 * e.g., "FLOOR_PLAN" -> "Floor Plan"
 */
export const formatDocumentType = (type: string): string => {
  return type
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

/**
 * Validity configuration for badges and icons
 */
export interface ValidityConfig {
  label: string;
  badgeBg: string;
  badgeColor: string;
  icon: LucideIcon;
}

/**
 * Get configuration for validity status badges
 */
export const getValidityConfig = (validity: string): ValidityConfig => {
  switch (validity.toUpperCase()) {
    case "VALID":
      return {
        label: "Valid",
        badgeBg: "rgba(59, 127, 115, 0.16)",
        badgeColor: "rgba(44, 124, 91, 1)",
        icon: CheckCircle2,
      };
    case "INVALID":
      return {
        label: "Invalid",
        badgeBg: "rgba(201, 86, 76, 0.16)",
        badgeColor: "rgba(156, 41, 34, 1)",
        icon: XCircle,
      };
    case "CLARIFICATION_NEEDED":
      return {
        label: "Needs review",
        badgeBg: "rgba(203, 162, 61, 0.16)",
        badgeColor: "rgba(124, 76, 20, 1)",
        icon: Loader2,
      };
    default:
      return {
        label: "Unknown",
        badgeBg: "rgba(128, 128, 128, 0.16)",
        badgeColor: "rgba(64, 64, 64, 1)",
        icon: Loader2,
      };
  }
};
