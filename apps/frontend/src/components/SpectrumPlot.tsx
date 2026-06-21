import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { DatasetData } from "../api";

const PALETTE = ["#4aa3ff", "#ff6b6b", "#51cf66", "#fcc419", "#b197fc", "#ff8787", "#22b8cf", "#a9e34b"];

// NMR & FTIR plot with a reversed abscissa by convention.
const REVERSED = new Set(["NMR", "FTIR"]);

function axisTitle(a: { label: string; unit: string | null }): string {
  return a.unit ? `${a.label} (${a.unit})` : a.label;
}

export function SpectrumPlot({ data }: { data: DatasetData }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const traces = data.signals.map((s, i) => ({
      x: s.points.map((p) => p[0]),
      y: s.points.map((p) => p[1]),
      type: "scattergl",
      mode: "lines",
      name: s.segment ?? s.name,
      line: { color: PALETTE[i % PALETTE.length], width: 1.4 },
    }));
    const x0 = data.signals[0]?.x;
    const y0 = data.signals[0]?.y;
    const layout = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#c9d1d9", size: 12 },
      margin: { l: 64, r: 16, t: 12, b: 48 },
      xaxis: {
        title: x0 ? axisTitle(x0) : "",
        autorange: REVERSED.has(data.technique) ? "reversed" : true,
        gridcolor: "#21262d",
        zeroline: false,
      },
      yaxis: { title: y0 ? axisTitle(y0) : "", gridcolor: "#21262d", zeroline: false },
      legend: { orientation: "h", y: -0.18 },
      showlegend: data.signals.length > 1,
    };
    Plotly.react(ref.current, traces as never, layout as never, {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["lasso2d", "select2d"],
    });
  }, [data]);

  return <div ref={ref} style={{ width: "100%", height: 480 }} />;
}
