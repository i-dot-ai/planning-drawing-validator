const API_BASE = "/api";

export class APIError extends Error {
  status: number;
  statusText: string;
  detail?: string;

  constructor(
    status: number,
    statusText: string,
    message?: string,
    detail?: string,
  ) {
    super(message || `API error: ${status} ${statusText}`);
    this.name = "APIError";
    this.status = status;
    this.statusText = statusText;
    this.detail = detail;
  }
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new APIError(response.status, response.statusText);
  }

  return response.json();
}

export const api = {
  evaluation: {
    getStatus: () => fetchJson<{ status: string }>("/evaluation/status"),
    getCurrentRun: () => fetchJson<{ documents: any[] }>("/evaluation/current"),
    start: (data?: any) =>
      fetchJson("/evaluation/start", {
        method: "POST",
        body: data ? JSON.stringify(data) : undefined,
      }),
    stop: () =>
      fetchJson("/evaluation/stop", {
        method: "POST",
      }),
  },
  runs: {
    getRuns: (_limit?: number) => fetchJson<{ runs: any[] }>("/runs"),
    getRun: (runId: string) =>
      fetchJson<{ documents: any[] }>(`/runs/${runId}`),
    deleteRun: (runId: string) =>
      fetchJson(`/runs/${runId}`, { method: "DELETE" }),
    deleteRuns: (runIds: string[]) =>
      fetchJson("/runs", {
        method: "DELETE",
        body: JSON.stringify({ run_ids: runIds }),
      }),
    exportRun: (runId: string) => fetchJson(`/runs/${runId}/export`),
    updateRunName: (runId: string, name: string) =>
      fetchJson(`/runs/${runId}`, {
        method: "PATCH",
        body: JSON.stringify({ name }),
      }),
    getStatsByModel: (groupByReasoningEffort: boolean = true) =>
      fetchJson<{ model_stats: any[] }>(
        `/runs/stats/by-model?group_by_reasoning_effort=${groupByReasoningEffort}`,
      ),
  },
  documents: {
    getDocuments: () => fetchJson<{ documents: any[] }>("/documents"),
    uploadDocuments: (files: FileList | File[]) => {
      const formData = new FormData();
      Array.from(files).forEach((file) => {
        formData.append("files", file);
      });
      return fetch(`${API_BASE}/documents/upload`, {
        method: "POST",
        body: formData,
      }).then((res) => {
        if (!res.ok) throw new APIError(res.status, res.statusText);
        return res.json();
      });
    },
  },
  groundTruth: {
    getGroundTruth: (path?: string) =>
      fetchJson<any>(
        path
          ? `/ground-truth?path=${encodeURIComponent(path)}`
          : "/ground-truth",
      ),
    saveGroundTruth: (dataDir: string, entries: any[]) =>
      fetchJson<{ ground_truth_path: string }>("/ground-truth", {
        method: "POST",
        body: JSON.stringify({ data_dir: dataDir, entries }),
      }),
    uploadGroundTruth: (
      file: File,
      columnConfig?: { filename?: string; validity?: string; reason?: string },
    ) => {
      const formData = new FormData();
      formData.append("file", file);
      // Build query params for column config
      const params = new URLSearchParams();
      if (columnConfig?.filename)
        params.append("filename_col", columnConfig.filename);
      if (columnConfig?.validity)
        params.append("validity_col", columnConfig.validity);
      if (columnConfig?.reason)
        params.append("reason_col", columnConfig.reason);
      const queryString = params.toString();
      const url = `${API_BASE}/ground-truth/upload${queryString ? `?${queryString}` : ""}`;
      return fetch(url, {
        method: "POST",
        body: formData,
      }).then((res) => {
        if (!res.ok) throw new APIError(res.status, res.statusText);
        return res.json();
      });
    },
  },
};
