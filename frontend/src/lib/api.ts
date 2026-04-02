const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

/**
 * Return a stable browser session ID (persisted in localStorage).
 * Each browser tab/device gets its own ID so users never see each other's data.
 */
function getSessionId(): string {
  if (typeof window === "undefined") return "";
  const KEY = "schemadoc_session_id";
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      "X-Session-ID": getSessionId(),
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));

    // Friendly message for rate-limited requests (429)
    if (res.status === 429) {
      throw new Error(
        "You're sending requests too quickly. Please wait a moment and try again.",
      );
    }

    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ── Pipeline ──
export async function runPipeline(connectionString: string) {
  return fetchAPI<PipelineRunResult>("/api/pipeline/run", {
    method: "POST",
    body: JSON.stringify({ connection_string: connectionString }),
  });
}

export async function getPipelineRun(runId: string) {
  return fetchAPI<PipelineRunResult>(`/api/pipeline/run/${runId}`);
}

export async function listPipelineRuns() {
  return fetchAPI<PipelineRunListItem[]>("/api/pipeline/runs");
}

export async function listDatabases() {
  return fetchAPI<{ databases: DatabaseInfo[] }>("/api/pipeline/databases");
}

// ── Schema ──
export async function getSchema(runId: string) {
  return fetchAPI<SchemaResult>(`/api/schema/${runId}`);
}

export async function getSchemaOverview(runId: string) {
  return fetchAPI<OverviewResult>(`/api/schema/${runId}/overview`);
}

export async function getTable(runId: string, tableName: string) {
  return fetchAPI<TableSchema>(`/api/schema/${runId}/table/${tableName}`);
}

// ── Chat ──
export async function sendChatMessage(
  message: string,
  runId: string,
  history: ChatMessage[],
) {
  return fetchAPI<ChatResponseData>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, run_id: runId, history }),
  });
}

// ── Export ──
export function getExportUrl(
  runId: string,
  format: "json" | "markdown",
): string {
  return `${API_URL}/api/export/${runId}/${format}`;
}

// ── Reports ──
export async function getBusinessReport(runId: string) {
  return fetchAPI<BusinessReport>(`/api/export/${runId}/report`);
}

export function getReportMarkdownUrl(runId: string): string {
  return `${API_URL}/api/export/${runId}/report/markdown`;
}

export function getReportJsonUrl(runId: string): string {
  return `${API_URL}/api/export/${runId}/report`;
}

// ── Health ──
export async function healthCheck() {
  return fetchAPI<{ status: string }>("/api/health");
}

// ── Aggregated API object ──
export const api = {
  runPipeline: (params: { db_path: string }) => runPipeline(params.db_path),
  getPipelineRun,
  listRuns: async (): Promise<PipelineRun[]> => {
    const runs = await listPipelineRuns();
    return runs.map((r: any) => ({
      run_id: r.run_id,
      status: r.status,
      created_at: r.created_at,
      result: r.schema_enriched ?? r.result ?? null,
      pipeline_log: (r.pipeline_log || []).map((e: any) =>
        typeof e === "string"
          ? {
              step: "info",
              status: "success",
              message: e,
              icon: "ℹ️",
              errors: [],
            }
          : {
              step: e.step || "info",
              status: e.status || "success",
              message: e.message || e.step,
              icon: e.icon || "ℹ️",
              errors: e.errors || [],
            },
      ),
    }));
  },
  listDatabases: async () => {
    const res = await listDatabases();
    return (res.databases || []).map((d: DatabaseInfo) => ({
      label: d.name || d.id,
      value: d.connection_string,
    }));
  },
  getSchema,
  getSchemaOverview,
  getTable,
  sendChatMessage: (params: { question: string; run_id: string }) =>
    sendChatMessage(params.question, params.run_id, []),
  getExportUrl,
  getBusinessReport,
  getReportMarkdownUrl,
  getReportJsonUrl,
  healthCheck,
  resetSession: async () => {
    const res = await fetch(`${API_URL}/api/reset`, {
      method: "POST",
      headers: { "X-Session-ID": getSessionId() },
    });
    if (!res.ok) throw new Error("Reset failed");
    return res.json();
  },
};

// ── Types ──
export interface PipelineRunResult {
  run_id: string;
  status: string;
  created_at: string;
  schema_enriched: Record<string, TableSchema> | null;
  pipeline_log: PipelineLogEntry[];
  errors: string[];
}

// Alias with `result` convenience field for pages
export interface PipelineRun {
  run_id: string;
  status: string;
  created_at: string;
  result: Record<string, any> | null;
  pipeline_log: PipelineLogEntry[];
}

export interface PipelineRunListItem {
  run_id: string;
  status: string;
  created_at: string;
}

export interface DatabaseInfo {
  id: string;
  name: string;
  connection_string: string;
  tables: number;
}

export interface SchemaResult {
  run_id: string;
  status: string;
  schema: Record<string, TableSchema> | null;
  pipeline_log: PipelineLogEntry[];
}

export interface OverviewResult {
  overview: string;
  total_tables: number;
  total_columns: number;
  total_rows: number;
  avg_health: number;
  pii_count: number;
  fk_count: number;
}

export interface TableSchema {
  table_name: string;
  row_count: number;
  columns: Record<string, ColumnMetadata>;
  health_score: number;
  foreign_keys: ForeignKey[];
  description: string | null;
}

export interface ColumnMetadata {
  name: string;
  original_type: string;
  description: string | null;
  business_logic: string | null;
  potential_pii: boolean;
  tags: string[];
  stats: ColumnStats | null;
}

export interface ColumnStats {
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_percentage: number;
  sample_values: string[];
  min_value: number | null;
  max_value: number | null;
  mean_value: number | null;
}

export interface ForeignKey {
  column: string;
  referred_table: string;
  referred_column: string;
}

export interface PipelineLogEntry {
  step: string;
  status: string;
  message: string;
  icon: string;
  errors: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponseData {
  response: string;
  sql_query: string | null;
}

// ── Business Report Types ──
export interface BusinessReport {
  report_metadata: {
    generated_at: string;
    run_id: string;
    generator: string;
    report_type: string;
  };
  executive_overview: {
    executive_summary: string;
    business_domain: string;
    key_findings: string[];
    recommendations: string[];
    data_governance_notes: string;
    overall_assessment: string;
  };
  database_statistics: {
    total_tables: number;
    total_columns: number;
    total_rows: number;
    average_health_score: number;
    pii_columns_detected: number;
    pii_column_list: string[];
    foreign_key_count: number;
  };
  quality_issues: QualityIssue[];
  relationships: Relationship[];
  tables: TableSummary[];
}

export interface QualityIssue {
  severity: "critical" | "warning";
  table: string;
  issue: string;
  recommendation: string;
}

export interface Relationship {
  source_table: string;
  source_column: string;
  target_table: string;
  target_column: string;
}

export interface TableSummary {
  table_name: string;
  description: string;
  row_count: number;
  column_count: number;
  health_score: number;
  foreign_keys: ForeignKey[];
  columns: ColumnDetail[];
}

export interface ColumnDetail {
  name: string;
  type: string;
  description: string;
  business_logic: string;
  tags: string[];
  potential_pii: boolean;
  null_percentage: number;
  unique_percentage: number;
  sample_values: string[];
  min_value: number | null;
  max_value: number | null;
  mean_value: number | null;
}
