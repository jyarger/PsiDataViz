import { useEffect, useRef, useState } from "react";
import * as $3Dmol from "3dmol";
import type { StructureData } from "../api";

// 3D molecular / crystal structure, rendered by 3Dmol.js from the raw structure-file text the backend
// ships (see psidata.readers.structure_file and comp_log geometry). Drag to rotate, scroll to zoom.
export function MoleculeViewer({ structure, title }: { structure: StructureData; title: string }) {
  const ref = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const viewerRef = useRef<any>(null);
  const [spin, setSpin] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let viewer: ReturnType<typeof $3Dmol.createViewer> | undefined;
    try {
      viewer = $3Dmol.createViewer(el, { backgroundColor: "#0d1117" });
      viewer.addModel(structure.data, structure.format);
      viewer.setStyle({}, { stick: { radius: 0.13 }, sphere: { scale: 0.27 } });
      viewer.zoomTo();
      viewer.render();
      viewerRef.current = viewer;
    } catch {
      setError(true);
    }
    const onResize = () => viewer?.resize();
    window.addEventListener("resize", onResize);
    return () => {
      window.removeEventListener("resize", onResize);
      try {
        viewer?.clear();
      } catch {
        /* noop */
      }
      if (el) el.innerHTML = "";
    };
  }, [structure]);

  useEffect(() => {
    const v = viewerRef.current;
    if (!v) return;
    v.spin(spin ? "y" : false);
  }, [spin]);

  return (
    <div className="mol-card">
      <div className="mol-head">
        <span className="mol-title">
          🧬 {title}
          {structure.n_atoms != null && <span className="mol-meta"> · {structure.n_atoms} atoms</span>}
          <span className="mol-meta"> · {structure.format.toUpperCase()}</span>
        </span>
        {!error && (
          <button className="mol-spin" onClick={() => setSpin((s) => !s)}>
            {spin ? "Stop" : "Spin"}
          </button>
        )}
      </div>
      {error ? (
        <div className="mol-fallback">
          3D view unavailable (WebGL not supported here). {structure.n_atoms ?? "?"} atoms ·{" "}
          {structure.format.toUpperCase()} structure.
        </div>
      ) : (
        <div ref={ref} className="mol-canvas" />
      )}
    </div>
  );
}
