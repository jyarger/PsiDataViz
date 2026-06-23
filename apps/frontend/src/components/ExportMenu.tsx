import { useState } from "react";
import { convertUrl } from "../api";

const FORMATS: [string, string][] = [
  ["CSDM (.csdf)", "csdf"],
  ["HDF5 (.h5)", "h5"],
  ["CSV — tidy", "csv"],
  ["Parquet", "parquet"],
  ["Feather", "feather"],
  ["CSV per signal (.zip)", "zip"],
];

export function ExportMenu({ url, name, technique }: { url: string; name: string; technique: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="export-menu" onMouseLeave={() => setOpen(false)}>
      <button className="btn ghost sm" onClick={() => setOpen((o) => !o)}>
        ⬇ Convert ▾
      </button>
      {open && (
        <div className="export-dropdown">
          {FORMATS.map(([label, fmt]) => (
            <a
              key={fmt}
              className="export-item"
              download
              href={convertUrl(url, name, technique, fmt)}
              onClick={() => setOpen(false)}
            >
              {label}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
