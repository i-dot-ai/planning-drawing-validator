export const WEBSOCKET_CONFIG = {
  DEV_PORT: 3000,
  BACKEND_PORT: 8000,
  RECONNECT_DELAY: 3000,
} as const;

export const CONNECTION_STATUS = {
  DISCONNECTED: "disconnected",
  CONNECTING: "connecting",
  CONNECTED: "connected",
} as const;

export type ConnectionStatus =
  (typeof CONNECTION_STATUS)[keyof typeof CONNECTION_STATUS];

export const WS_MESSAGE_TYPES = {
  EVALUATION_STARTED: "evaluation_started",
  DOCUMENT_STARTED: "document_started",
  STAGE_STARTED: "stage_started",
  STAGE_COMPLETED: "stage_completed",
  DOCUMENT_COMPLETED: "document_completed",
  DOCUMENT_ERROR: "document_error",
  QUEUE_STATUS: "queue_status",
  EVALUATION_COMPLETED: "evaluation_completed",
  EVALUATION_STOPPED: "evaluation_stopped",
} as const;

export const EVALUATION_STAGES = {
  CLASSIFICATION: {
    id: "classification",
    name: "Classification",
  },
  VALIDATION: {
    id: "validation",
    name: "Validation",
  },
} as const;
