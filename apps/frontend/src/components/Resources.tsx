export function Resources({ onClose }: { onClose: () => void }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h2>
            <span className="psi">Ψ</span> Resources
          </h2>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <section>
          <h3>Getting started</h3>
          <p>
            On the <b>QUICK</b> tab, paste a public <b>GitHub repo</b> or <b>Google Drive folder</b> URL
            and click <b>Scan</b> — or use one of the <b>Try</b> presets. PsiDataViz groups files that
            share a base name into one dataset, lets you <b>filter</b>, <b>overlay</b>, and <b>compare</b>
            them, and <b>convert</b> to standard formats. The default source is the Yarger Lab data repo.
          </p>
        </section>

        <section>
          <h3>FAIR data &amp; open repositories</h3>
          <p>
            PsiDataViz follows the <b>FAIR</b> principles — data should be{" "}
            <b>Findable</b>, <b>Accessible</b>, <b>Interoperable</b>, and <b>Reusable</b>. There are two
            ways to bring data in:
          </p>
          <ul>
            <li>
              <b>Host your own data</b> — point the app at a public folder you control (GitHub, Google
              Drive, Codeberg, Box).
            </li>
            <li>
              <b>Open FAIR repositories</b> — access published, DOI-minted datasets from open
              repositories (e.g. the <b>Chemotion</b> repository), with more on the way.
            </li>
          </ul>
          <p>
            Discover FAIR-aligned databases, repositories, and standards at{" "}
            <a href="https://fairsharing.org/" target="_blank" rel="noreferrer">
              fairsharing.org
            </a>{" "}
            and read the principles at{" "}
            <a href="https://www.go-fair.org/fair-principles/" target="_blank" rel="noreferrer">
              go-fair.org
            </a>
            .
          </p>
        </section>

        <section>
          <h3>Supported formats</h3>
          <ul>
            <li><b>DSC</b> — TA Trios <code>.txt</code> / <code>.csv</code></li>
            <li><b>NMR</b> — JCAMP-DX (<code>.jdx/.dx/.txt</code>, incl. compressed ASDF), <code>.tsv</code>, TopSpin 2D <code>totxt</code></li>
            <li><b>FTIR</b> — Bruker <code>.dpt</code>, IR JCAMP <code>.jdx/.dx</code>, PerkinElmer <code>.asc</code>, <code>.csv</code></li>
            <li><b>Raman</b> — <code>.csv</code></li>
          </ul>
        </section>

        <section>
          <h3>Example data sources</h3>
          <ul>
            <li>
              <a href="https://github.com/yargerlab/Data" target="_blank" rel="noreferrer">
                github.com/yargerlab/Data
              </a>{" "}
              — Yarger Lab instrument data (the default).
            </li>
            <li>
              <a
                href="https://drive.google.com/drive/folders/16VQhcRbCHkzhH2cq8T5DwyhTUBj2BrO4"
                target="_blank"
                rel="noreferrer"
              >
                Google Drive — Psi_Data
              </a>{" "}
              — shared example folder, scannable directly (no API key needed).
            </li>
            <li>
              <a href="https://www.chemotion-repository.net/" target="_blank" rel="noreferrer">
                Chemotion repository
              </a>{" "}
              — an open FAIR repository of published chemistry data (NMR, IR, MS).
            </li>
          </ul>
        </section>

        <section>
          <h3>Convert &amp; export</h3>
          <p>
            Any dataset can be downloaded as <b>CSDM</b>, <b>HDF5</b>, <b>CSV</b>, <b>Parquet</b>,{" "}
            <b>Feather</b>, or per-signal <b>CSV (zip)</b> from the plot's <b>Convert</b> menu — or taken
            into a notebook for advanced analysis with <b>Open in… → Colab / marimo</b>, which generates a
            runnable notebook that re-fetches and re-plots your selection with <code>psidata</code>.
          </p>
        </section>

        <section>
          <h3>Adding a reader</h3>
          <p>
            New instrument formats are added to the <code>psidata</code> Python library by writing one
            reader (a <code>sniff()</code> + <code>read()</code> pair) and registering it — the catalog
            and app pick it up automatically, no UI changes needed.
          </p>
        </section>
      </div>
    </div>
  );
}
