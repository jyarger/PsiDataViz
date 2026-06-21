import { useState } from "react";
import { api, type DatasetData, type RecordRow, type ScanResult } from "./api";
import { Header, type View } from "./components/Header";
import { Footer } from "./components/Footer";
import { SpectrumPlot } from "./components/SpectrumPlot";

const DEFAULT_REPO = "https://github.com/yargerlab/Data";

export default function App() {
  const [view, setView] = useState<View>("QUICK");
  return (
    <>
      <Header view={view} onNav={setView} />
      <main className="main">{view === "QUICK" ? <Quick /> : <Coming view={view} />}</main>
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
        Start from <b>QUICK</b> to point at a data source and visualize.
      </p>
    </div>
  );
}

function Quick() {
  const [repo, setRepo] = useState(DEFAULT_REPO);
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [technique, setTechnique] = useState<string | null>(null);
  const [records, setRecords] = useState<RecordRow[]>([]);
  const [selected, setSelected] = useState<RecordRow | null>(null);
  const [dataset, setDataset] = useState<DatasetData | null>(null);
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

  async function doScan() {
    setScan(null); setTechnique(null); setRecords([]); setSelected(null); setDataset(null);
    const result = await run("Scanning repository…", () => api.scan(repo));
    if (result) {
      setScan(result);
      const first = result.techniques.find((t) => t.n_supported > 0)?.technique;
      if (first) void pickTechnique(first);
    }
  }

  async function pickTechnique(t: string) {
    setTechnique(t); setSelected(null); setDataset(null);
    const rows = await run("Loading datasets…", () => api.records(repo, t));
    if (rows) setRecords(rows);
  }

  async function pickRecord(r: RecordRow) {
    setSelected(r);
    const ds = await run("Parsing dataset…", () => api.dataset(repo, r.name, r.technique));
    if (ds) setDataset(ds);
  }

  return (
    <>
      <h1>Point at a data source</h1>
      <p className="subtitle">
        Scan a public repository of scientific data and visualize it instantly.
      </p>

      <div className="row">
        <input
          type="text"
          value={repo}
          onChange={(e) => setRepo(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doScan()}
          placeholder="owner/repo or https://github.com/owner/repo"
        />
        <button className="btn" onClick={doScan} disabled={!!busy}>
          Scan
        </button>
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
        <div className="card">
          <p className="section-title">{technique} datasets ({records.length})</p>
          <div className="scroll">
            <table>
              <thead>
                <tr><th>Date</th><th>Sample / description</th><th>Formats</th></tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr
                    key={r.key}
                    className={selected?.key === r.key ? "selected" : ""}
                    onClick={() => pickRecord(r)}
                  >
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

      {dataset && (
        <div className="card">
          <p className="section-title">
            {dataset.filename} · {dataset.technique} · {dataset.signals.length} signal
            {dataset.signals.length === 1 ? "" : "s"}{" "}
            <span className="muted">(reader: {dataset.reader})</span>
          </p>
          <SpectrumPlot data={dataset} />
          <Metadata meta={dataset.metadata} />
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
