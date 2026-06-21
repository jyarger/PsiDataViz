import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { DatasetData } from "../api";

const PALETTE = ["#4aa3ff", "#ff6b6b", "#51cf66", "#fcc419", "#b197fc", "#ff8787", "#22b8cf", "#a9e34b"];

// NMR & FTIR plot with a reversed abscissa by convention.
const REVERSED = new Set(["NMR", "FTIR"]);

function axisTitle(a: { label: string; unit: string | null }): string {
  return a.unit ? `${a.label} (${a.unit})` : a.label;
}

function normalizeY(ys: number[]): number[] {
  let lo = Infinity;
  let hi = -Infinity;
  for (const v of ys) {
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  const span = hi - lo || 1;
  return ys.map((v) => (v - lo) / span);
}

export function SpectrumPlot({
  datasets,
  normalize = false,
}: {
  datasets: DatasetData[];
  normalize?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || datasets.length === 0) return;
    const multi = datasets.length > 1;
    let color = 0;
    const traces = datasets.flatMap((ds) => {
      const label = ds.metadata.sample_name ? String(ds.metadata.sample_name) : ds.filename;
      return ds.signals.map((s) => {
        const segLabel = s.segment ?? s.name;
        const name = multi ? `${label} · ${segLabel}` : segLabel;
        const ys = s.points.map((p) => p[1]);
        return {
          x: s.points.map((p) => p[0]),
          y: normalize ? normalizeY(ys) : ys,
          type: "scattergl",
          mode: "lines",
          name,
          line: { color: PALETTE[color++ % PALETTE.length], width: 1.4 },
        };
      });
    });

    const x0 = datasets[0].signals[0]?.x;
    const y0 = datasets[0].signals[0]?.y;
    const yTitle = y0 ? (normalize ? `${y0.label} (normalized)` : axisTitle(y0)) : "";
    const layout = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#c9d1d9", size: 12 },
      margin: { l: 64, r: 16, t: 12, b: 48 },
      xaxis: {
        title: x0 ? axisTitle(x0) : "",
        autorange: REVERSED.has(datasets[0].technique) ? "reversed" : true,
        gridcolor: "#21262d",
        zeroline: false,
      },
      yaxis: { title: yTitle, gridcolor: "#21262d", zeroline: false },
      legend: { orientation: "h", y: -0.18 },
      showlegend: traces.length > 1,
    };
    Plotly.react(ref.current, traces as never, layout as never, {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["lasso2d", "select2d"],
    });
  }, [datasets, normalize]);

  return <div ref={ref} style={{ width: "100%", height: 480 }} />;
}
