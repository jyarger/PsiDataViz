import { useState } from "react";
import { api, type RepoSearchResult } from "../api";

const REPOS = [{ id: "zenodo", label: "Zenodo" }];

// Search open FAIR repositories for published records and visualize one — distinct from scanning a
// folder you host. Results are summaries (no downloads); "Visualize" scans that record via <repo>:<id>.
export function RepoSearch({ onPick, busy }: { onPick: (url: string) => void; busy?: boolean }) {
  const [repo, setRepo] = useState("zenodo");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [result, setResult] = useState<RepoSearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search(p = 1) {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await api.repoSearch(repo, query.trim(), p));
      setPage(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="repo-search">
      <div className="repo-search-bar">
        <select value={repo} onChange={(e) => setRepo(e.target.value)} title="Repository">
          {REPOS.map((r) => (
            <option key={r.id} value={r.id}>
              {r.label}
            </option>
          ))}
        </select>
        <input
          type="text"
          value={query}
          placeholder="Search open repositories — e.g. Raman olivine, FTIR cellulose, NMR caffeine"
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search(1)}
        />
        <button className="btn" onClick={() => search(1)} disabled={loading || !query.trim()}>
          Search
        </button>
      </div>

      {loading && <p className="spinner">Searching {repo}…</p>}
      {error && <p className="error">{error}</p>}

      {result && !loading && (
        <>
          <div className="repo-results-head">
            {result.total.toLocaleString()} result{result.total === 1 ? "" : "s"} · page {result.page}
          </div>
          <div className="repo-results">
            {result.records.length === 0 && <p className="muted">No records found — try other terms.</p>}
            {result.records.map((r) => (
              <div className="repo-result" key={r.id}>
                <div className="repo-result-main">
                  <a
                    href={r.url ?? "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="repo-result-title"
                  >
                    {r.title}
                  </a>
                  <div className="repo-result-meta">
                    {r.authors.slice(0, 3).join(", ")}
                    {r.authors.length > 3 ? " et al." : ""}
                    {r.published && ` · ${r.published}`}
                    {r.resource_type && ` · ${r.resource_type}`}
                    {` · ${r.n_files} file${r.n_files === 1 ? "" : "s"}`}
                  </div>
                  {r.doi && <div className="repo-result-doi">{r.doi}</div>}
                </div>
                <button
                  className="btn ghost sm"
                  disabled={busy || r.n_files === 0}
                  title={r.n_files === 0 ? "No files to visualize" : "Scan & visualize this record"}
                  onClick={() => onPick(`${repo}:${r.id}`)}
                >
                  Visualize →
                </button>
              </div>
            ))}
          </div>
          <div className="repo-pager">
            <button className="btn ghost sm" disabled={page <= 1 || loading} onClick={() => search(page - 1)}>
              ‹ Prev
            </button>
            <button
              className="btn ghost sm"
              disabled={loading || result.records.length < result.per_page}
              onClick={() => search(page + 1)}
            >
              Next ›
            </button>
          </div>
        </>
      )}
    </div>
  );
}
