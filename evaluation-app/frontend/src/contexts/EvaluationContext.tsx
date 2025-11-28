import React, { createContext, useContext, ReactNode } from "react";
import { DocumentEvaluation, WebSocketMessage } from "../types";
import { useEvaluation } from "../hooks/useEvaluation";
import { useWebSocket } from "../hooks/useWebSocket";

interface EvaluationContextType {
  evaluations: DocumentEvaluation[];
  setEvaluations: React.Dispatch<React.SetStateAction<DocumentEvaluation[]>>;
  isRunning: boolean;
  setIsRunning: React.Dispatch<React.SetStateAction<boolean>>;
  currentRunId: string;
  documentQueue: ReturnType<typeof useEvaluation>["documentQueue"];
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  liveMetrics: ReturnType<typeof useEvaluation>["liveMetrics"];
  connectionStatus: "disconnected" | "connecting" | "connected";
}

const EvaluationContext = createContext<EvaluationContextType | undefined>(
  undefined,
);

export function EvaluationProvider({ children }: { children: ReactNode }) {
  const {
    evaluations,
    setEvaluations,
    isRunning,
    setIsRunning,
    currentRunId,
    documentQueue,
    handleWebSocketMessage,
    liveMetrics,
  } = useEvaluation();

  const { connectionStatus } = useWebSocket(handleWebSocketMessage);

  return (
    <EvaluationContext.Provider
      value={{
        evaluations,
        setEvaluations,
        isRunning,
        setIsRunning,
        currentRunId,
        documentQueue,
        handleWebSocketMessage,
        liveMetrics,
        connectionStatus,
      }}
    >
      {children}
    </EvaluationContext.Provider>
  );
}

export function useEvaluationContext() {
  const context = useContext(EvaluationContext);
  if (context === undefined) {
    throw new Error(
      "useEvaluationContext must be used within an EvaluationProvider",
    );
  }
  return context;
}
