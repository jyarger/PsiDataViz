// Typed client for the PsiData FastAPI backend (proxied at /api in dev).

export interface Technique {
  technique: string;
  n_datasets: number;
  n_supported: number;
}
export interface ScanResult {
  source: string;
  n_files: number;
  n_records: number;
  n_data_records: number;
  n_supported_records: number;
  techniques: Technique[];
}
export interface RecordRow {
  key: string;
  technique: string;
  date: string | null;
  description: string;
  formats: string[];
  extras: string[];
  primary: string;
  name: string;
  url: string;
}
export interface CatalogResult extends ScanResult {
  records: RecordRow[];
}
export interface AxisInfo {
  label: string;
  unit: string | null;
  quantity: string | null;
}
export interface SignalData {
  name: string;
  segment: string | null;
  x: AxisInfo;
  y: AxisInfo;
  points: [number, number][];
}
export interface DatasetData {
  technique: string;
  filename: string;
  reader: string;
  metadata: Record<string, unknown>;
  signals: SignalData[];
}

export interface FormatComparison {
  identical?: boolean;
  summary?: string;
  differences?: string[];
  error?: string;
}
export interface CompareResult {
  comparable: boolean;
  reason?: string;
  technique?: string;
  primary?: string;
  formats: string[];
  comparisons?: Record<string, FormatComparison>;
  summary?: string;
}

const BASE = import.meta.env.VITE_API_BASE ?? "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const b = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(b.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

const q = encodeURIComponent;

export const api = {
  scan: (url: string) => get<ScanResult>(`/api/scan?url=${q(url)}`),
  catalog: (url: string) => get<CatalogResult>(`/api/catalog?url=${q(url)}`),
  records: (url: string, technique: string) =>
    get<RecordRow[]>(`/api/records?url=${q(url)}&technique=${q(technique)}`),
  dataset: (url: string, name: string, technique: string) =>
    get<DatasetData>(`/api/dataset?url=${q(url)}&name=${q(name)}&technique=${q(technique)}`),
  compare: (url: string, technique: string, key: string) =>
    post<CompareResult>(`/api/compare`, { url, technique, key }),
};

// Direct download URL for converting a dataset to a standard format (csdf | h5).
export function convertUrl(url: string, name: string, technique: string, fmt: string): string {
  return `${BASE}/api/convert?url=${q(url)}&name=${q(name)}&technique=${q(technique)}&fmt=${fmt}`;
}
