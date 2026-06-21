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

const BASE = import.meta.env.VITE_API_BASE ?? "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

const q = encodeURIComponent;

export const api = {
  scan: (url: string) => get<ScanResult>(`/api/scan?url=${q(url)}`),
  records: (url: string, technique: string) =>
    get<RecordRow[]>(`/api/records?url=${q(url)}&technique=${q(technique)}`),
  dataset: (url: string, name: string, technique: string) =>
    get<DatasetData>(`/api/dataset?url=${q(url)}&name=${q(name)}&technique=${q(technique)}`),
};
