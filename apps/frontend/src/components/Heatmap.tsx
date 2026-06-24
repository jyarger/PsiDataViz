import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { DatasetData } from "../api";

// A 2D detector image (XRD/SAXS/WAXS area-detector frame) as a heatmap. The backend sends a
// downsampled, log-scaled intensity grid (see services._image_json).
export function Heatmap({ dataset }: { dataset: DatasetData }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || !dataset.images?.length) return;
    const im = dataset.images[0];
    const axisTitle = (a: { label: string; unit: string | null }) =>
      a.unit ? `${a.label} (${a.unit})` : a.label;

    const trace = {
      z: im.values,
      type: "heatmap",
      colorscale: "Viridis",
      colorbar: { title: { text: `${im.z.label} (log)`, side: "right" }, tickfont: { size: 11 } },
    };
    const layout = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#c9d1d9", size: 12 },
      margin: { l: 56, r: 16, t: 12, b: 48 },
      xaxis: { title: { text: axisTitle(im.x), font: { size: 15 } }, tickfont: { size: 13 }, constrain: "domain" },
      yaxis: {
        title: { text: axisTitle(im.y), font: { size: 15 } },
        tickfont: { size: 13 },
        autorange: "reversed", // image convention: row 0 at top
        scaleanchor: "x", // square pixels
        constrain: "domain",
      },
    };
    Plotly.react(ref.current, [trace] as never, layout as never, {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["lasso2d", "select2d"],
    });
  }, [dataset]);

  return <div ref={ref} style={{ width: "100%", height: 540 }} />;
}
