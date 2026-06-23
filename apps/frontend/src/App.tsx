import { useState } from "react";
import {
  api,
  type CompareResult,
  type DatasetData,
  type RecordRow,
  type ScanResult,
} from "./api";
import { Header, type View } from "./components/Header";
import { Footer } from "./components/Footer";
import { SpectrumPlot } from "./components/SpectrumPlot";
import { CompareView } from "./components/CompareView";
import { ExportMenu } from "./components/ExportMenu";

const DEFAULT_REPO = "https://github.com/yargerlab/Data";

function PanelBrand({ label }: { label: string }) {
  return (
    <div className="panel-brand">
      <span className="psi">Ψ</span>
      {label}
    </div>
  );
}

export default function App() {
  const [view, setView] = useState<View>("QUICK");
  return (
    <>
      <Header view={view} onNav={setView} />
      <main className="main">
        {/* keep QUICK mounted (hidden) so scan/plot state survives tab switches */}
        <div hidden={view !== "QUICK"}>
          <Quick />
        </div>
        {view !== "QUICK" && <Coming view={view} />}
      </main>
      <Footer />
    </>
  );
}

function Coming({ view }: { view: View }) {
  return (
    <div className="card">
      <p className="coming">
        <b>{view}</b> — advanced {view.toLowerCase()} features are coming soon.
        <br />
        Start from <b>QUICK</b> to point at a data source, overlay datasets, and compare formats.
      </p>
    </div>
  );
}

const PRESETS: { label: string; icon: string; url: string }[] = [
  { label: "yargerlab/Data", icon: "GH", url: "https://github.com/yargerlab/Data" },
  {
    label: "Google Drive — Psi_Data",
    icon: "▲",
    url: "https://drive.google.com/drive/folders/16VQhcRbCHkzhH2cq8T5DwyhTUBj2BrO4",
  },
];

function Quick() {
  const [repo, setRepo] = useState(DEFAULT_REPO);
  const [src, setSrc] = useState(DEFAULT_REPO); // the source URL backing the current scan
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [technique, setTechnique] = useState<string | null>(null);
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [selected, setSelected] = useState<string[]>([]); // ordered record keys
  const [datasets, setDatasets] = useState<Record<string, DatasetData>>({});
  const [compare, setCompare] = useState<CompareResult | null>(null);
  const [filter, setFilter] = useState("");
  const [normalize, setNormalize] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run<T>(what: string, fn: () => Promise<T>): Promise<T | undefined> {
    setBusy(what);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  function clearSelection() {
    setSelected([]);
    setDatasets({});
    setCompare(null);
  }

  async function doScan(target?: string) {
    const url = (target ?? repo).trim();
    setRepo(url);
    setSrc(url);
    setScan(null);
    setTechnique(null);
    setRecords([]);
    clearSelection();
    const result = await run("Scanning data source…", () => api.scan(url));
    if (result) {
      setScan(result);
      const first = result.techniques.find((t) => t.n_supported > 0)?.technique;
      if (first) void pickTechnique(first, url);
    }
  }

  async function pickTechnique(t: string, source: string = src) {
    setTechnique(t);
    clearSelection();
    const rows = await run("Loading datasets…", () => api.records(source, t));
    if (rows) setRecords(rows);
  }

  async function toggleRecord(r: RecordRow) {
    setCompare(null);
    if (selected.includes(r.key)) {
      setSelected(selected.filter((k) => k !== r.key));
      setDatasets((d) => {
        const next = { ...d };
        delete next[r.key];
        return next;
      });
      return;
    }
    const ds = await run("Parsing dataset…", () => api.dataset(r.url, r.name, r.technique));
    if (ds) {
      setSelected((s) => [...s, r.key]);
      setDatasets((d) => ({ ...d, [r.key]: ds }));
    }
  }

  async function doCompare() {
    const r = selected.length === 1 ? records.find((x) => x.key === selected[0]) : null;
    if (!r) return;
    const res = await run("Comparing formats…", () => api.compare(src, r.technique, r.key));
    if (res) setCompare(res);
  }

  const selectedDatasets = selected.map((k) => datasets[k]).filter(Boolean);
  const soleRecord = selected.length === 1 ? records.find((r) => r.key === selected[0]) : null;
  const canCompare = !!soleRecord && soleRecord.formats.length > 1;
  const needle = filter.trim().toLowerCase();
  const shown = needle
    ? records.filter(
        (r) => r.description.toLowerCase().includes(needle) || (r.date ?? "").includes(needle),
      )
    : records;

  return (
    <>
      <h1>Point at a data source</h1>
      <p className="subtitle">
        Scan a public repository, overlay datasets, and compare formats — instantly.
      </p>

      <div className="row">
        <input
          type="text"
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doScan()}
          placeholder="GitHub repo (owner/repo) or a public Google Drive folder URL"
        />
        <button className="btn" onClick={() => doScan()} disabled={!!busy}>
          Scan
        </button>
      </div>
      <div className="presets">
        <span className="muted">Try:</span>
        {PRESETS.map((p) => (
          <button
            key={p.url}
            className="src-chip"
            onClick={() => doScan(p.url)}
            disabled={!!busy}
            title={p.url}
          >
            <span className="src-ic">{p.icon}</span>
            {p.label}
          </button>
        ))}
      </div>

      {busy && <p className="spinner">{busy}</p>}
      {error && <p className="error">{error}</p>}

      {scan && (
        <div className="card">
          <p>
            <b>{scan.n_data_records.toLocaleString()}</b> datasets from{" "}
            {scan.n_files.toLocaleString()} files —{" "}
            <span className="muted">
              files sharing a base name across formats count as one dataset.
            </span>
          </p>
          <div className="chips">
            {scan.techniques
              .filter((t) => t.n_supported > 0)
              .map((t) => (
                <span
                  key={t.technique}
                  className={"chip" + (t.technique === technique ? " active" : "")}
                  onClick={() => pickTechnique(t.technique)}
                >
                  {t.technique}
                  <span className="count">{t.n_supported}</span>
                </span>
              ))}
          </div>
        </div>
      )}

      {records.length > 0 && (
        <div className="card with-brand">
          <PanelBrand label="PsiData" />
          <div className="toolbar">
            <span className="section-title" style={{ margin: 0 }}>
              {technique} datasets ({needle ? `${shown.length} of ${records.length}` : records.length}){" "}
              <span className="muted">— click to overlay</span>
            </span>
            <input
              type="text"
              className="filter"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="filter by sample or date…"
            />
          </div>
          <div className="scroll">
            <table>
              <thead>
                <tr>
                  <th style={{ width: 28 }}></th>
                  <th>Date</th>
                  <th>Sample / description</th>
                  <th>Formats</th>
                </tr>
              </thead>
              <tbody>
                {shown.map((r) => (
                  <tr
                    key={r.key}
                    className={selected.includes(r.key) ? "selected" : ""}
                    onClick={() => toggleRecord(r)}
                  >
                    <td>
                      <input type="checkbox" readOnly checked={selected.includes(r.key)} />
                    </td>
                    <td>{r.date ?? ""}</td>
                    <td>{r.description}</td>
                    <td className="fmt">
                      {r.formats.join(", ")}
                      {r.extras.length > 0 && <span className="extra"> (+{r.extras.join(", ")})</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedDatasets.length > 0 && (
        <div className="card with-brand">
          <PanelBrand label="PsiViz" />
          <div className="toolbar">
            <span className="section-title" style={{ margin: 0 }}>
              {selectedDatasets.length} dataset{selectedDatasets.length === 1 ? "" : "s"} overlaid
            </span>
            <div className="row" style={{ gap: 12 }}>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={normalize}
                  onChange={(e) => setNormalize(e.target.checked)}
                />
                Normalize
              </label>
              {canCompare && (
                <button className="btn ghost" onClick={doCompare} disabled={!!busy}>
                  Compare formats
                </button>
              )}
              <button className="btn ghost" onClick={clearSelection}>
                Clear
              </button>
            </div>
          </div>
          <SpectrumPlot datasets={selectedDatasets} normalize={normalize} />
          {compare && (
            <div className="cmp-panel">
              <CompareView result={compare} />
            </div>
          )}
          {soleRecord && datasets[soleRecord.key] && (
            <>
              <div className="export-row">
                <span className="muted">Convert to standard format:</span>
                <ExportMenu
                  url={soleRecord.url}
                  name={soleRecord.name}
                  technique={soleRecord.technique}
                />
              </div>
              <Metadata meta={datasets[soleRecord.key].metadata} />
            </>
          )}
        </div>
      )}
    </>
  );
}

function Metadata({ meta }: { meta: Record<string, unknown> }) {
  const rows = Object.entries(meta).filter(([, v]) => typeof v !== "object");
  if (rows.length === 0) return null;
  return (
    <dl className="meta">
      {rows.map(([k, v]) => (
        <div style={{ display: "contents" }} key={k}>
          <dt>{k.replace(/_/g, " ")}</dt>
          <dd>{String(v)}</dd>
        </div>
      ))}
    </dl>
  );
}
