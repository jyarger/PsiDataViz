export type View = "QUICK" | "DATA" | "VIZ";

// The two advanced tabs use Dirac bracket-ket wordmarks: Ψ|Data⟩ and Ψ|Viz⟩.
const ITEMS: { id: View; label: string; ket?: string }[] = [
  { id: "QUICK", label: "QUICK" },
  { id: "DATA", label: "Data", ket: "|Data⟩" },
  { id: "VIZ", label: "Viz", ket: "|Viz⟩" },
];

export function Header({ view, onNav }: { view: View; onNav: (v: View) => void }) {
  return (
    <header className="header">
      <div className="brand" onClick={() => onNav("QUICK")} role="button" tabIndex={0}>
        <span className="psi">Ψ</span>
        <span className="brand-ket">|DataViz⟩</span>
        <small>Scientific Data Visualization</small>
      </div>
      <nav className="nav">
        {ITEMS.map((it) => (
          <button key={it.id} className={it.id === view ? "active" : ""} onClick={() => onNav(it.id)}>
            {it.ket ? (
              <>
                <span className="psi">Ψ</span>
                <span className="ket">{it.ket}</span>
              </>
            ) : (
              it.label
            )}
          </button>
        ))}
        <button className="nav-soon" disabled title="Sign in / register — coming soon">
          <span className="psi">Ψ</span>
          <span className="ket">|Login⟩</span>
        </button>
      </nav>
    </header>
  );
}
