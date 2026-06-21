export const NAV = ["QUICK", "DATA", "ANALYSIS", "VISUALIZATION", "ADVANCED"] as const;
export type View = (typeof NAV)[number];

export function Header({ view, onNav }: { view: View; onNav: (v: View) => void }) {
  return (
    <header className="header">
      <div className="brand">
        <span className="psi">Ψ</span>DataViz
        <small>Scientific Data Visualization</small>
      </div>
      <nav className="nav">
        {NAV.map((item) => (
          <button
            key={item}
            className={item === view ? "active" : ""}
            onClick={() => onNav(item)}
          >
            {item}
          </button>
        ))}
      </nav>
    </header>
  );
}
