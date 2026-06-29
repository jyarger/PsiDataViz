import { useState } from "react";
import { exportNotebook, type NotebookDataset } from "../api";

const FORMATS = [
  { fmt: "colab" as const, label: "Colab / Jupyter (.ipynb)", ext: "ipynb" },
  { fmt: "marimo" as const, label: "marimo (.py)", ext: "py" },
];

// "Open in…" — generates a self-contained notebook that re-fetches and re-plots the selected datasets
// with psidata, so the user can carry the data into Colab or marimo for advanced analysis.
export function NotebookMenu({ datasets }: { datasets: NotebookDataset[] }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  if (datasets.length === 0) return null;

  async function download(fmt: "colab" | "marimo", ext: string) {
    setOpen(false);
    setBusy(fmt);
    try {
      const blob = await exportNotebook({ datasets, fmt });
      const href = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = href;
      a.download = `psidata_export.${ext}`;
      a.click();
      URL.revokeObjectURL(href);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Notebook export failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="export-menu" onMouseLeave={() => setOpen(false)}>
      <button className="btn ghost sm" onClick={() => setOpen((o) => !o)}>
        📓 Open in… ▾
      </button>
      {open && (
        <div className="export-dropdown">
          <div className="export-group">Notebook — loads &amp; plots this data</div>
          {FORMATS.map((f) => (
            <button
              key={f.fmt}
              className="export-item"
              onClick={() => download(f.fmt, f.ext)}
              disabled={busy === f.fmt}
            >
              {busy === f.fmt ? "…" : f.label}
            </button>
          ))}
          <div className="export-hint">
            Colab: upload the .ipynb at colab.research.google.com · marimo: <code>marimo edit --sandbox</code>
          </div>
        </div>
      )}
    </div>
  );
}
