import { useState, useCallback } from "react";

/**
 * Document in the processing queue
 */
export interface QueuedDocument {
  document_id: string;
  filename: string;
  status: "pending" | "processing" | "completed" | "error";
}

/**
 * Custom hook for managing the document processing queue
 *
 * Provides state and operations for tracking document processing status
 * during evaluation runs.
 *
 * @returns Queue state and management functions
 */
export function useDocumentQueue() {
  const [documentQueue, setDocumentQueue] = useState<QueuedDocument[]>([]);

  /**
   * Initialize the queue with documents
   */
  const initializeQueue = useCallback(
    (documents: Array<{ document_id: string; filename: string }>) => {
      setDocumentQueue(
        documents.map((doc) => ({
          document_id: doc.document_id,
          filename: doc.filename,
          status: "pending" as const,
        })),
      );
    },
    [],
  );

  /**
   * Mark a document as processing
   */
  const markAsProcessing = useCallback(
    (documentId: string, filename?: string) => {
      setDocumentQueue((prev) => {
        const docIndex = prev.findIndex(
          (doc) => doc.document_id === documentId || doc.filename === filename,
        );
        if (docIndex === -1) return prev; // Document not found

        const doc = prev[docIndex];
        // Check if already processing
        if (doc.status === "processing") {
          return prev; // No change needed
        }

        // Create new array only if status changed
        const updated = [...prev];
        updated[docIndex] = { ...doc, status: "processing" as const };
        return updated;
      });
    },
    [],
  );

  /**
   * Mark a document as completed and remove from queue
   */
  const markAsCompleted = useCallback((documentId: string) => {
    setDocumentQueue((prev) => {
      // Check if document exists in queue
      const exists = prev.some((doc) => doc.document_id === documentId);
      if (!exists) return prev; // Already removed, no change

      // Remove the document
      return prev.filter((doc) => doc.document_id !== documentId);
    });
  }, []);

  /**
   * Mark a document as error
   */
  const markAsError = useCallback((documentId: string) => {
    setDocumentQueue((prev) => {
      const docIndex = prev.findIndex((doc) => doc.document_id === documentId);
      if (docIndex === -1) return prev; // Document not found

      const doc = prev[docIndex];
      // Check if already in error state
      if (doc.status === "error") {
        return prev; // No change needed
      }

      // Create new array only if status changed
      const updated = [...prev];
      updated[docIndex] = { ...doc, status: "error" as const };
      return updated;
    });
  }, []);

  /**
   * Clear the entire queue
   */
  const clearQueue = useCallback(() => {
    setDocumentQueue([]);
  }, []);

  /**
   * Get queue statistics
   */
  const getQueueStats = useCallback(() => {
    const total = documentQueue.length;
    const pending = documentQueue.filter((d) => d.status === "pending").length;
    const processing = documentQueue.filter(
      (d) => d.status === "processing",
    ).length;
    const errors = documentQueue.filter((d) => d.status === "error").length;

    return { total, pending, processing, errors };
  }, [documentQueue]);

  return {
    documentQueue,
    setDocumentQueue,
    initializeQueue,
    markAsProcessing,
    markAsCompleted,
    markAsError,
    clearQueue,
    getQueueStats,
  };
}
