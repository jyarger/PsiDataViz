import { useState } from "react";

type Provider = {
  id: string;
  label: string;
  icon: string;
  ready: boolean;
  example?: string;
  steps?: { title: string; items: string[] };
};

const PROVIDERS: Provider[] = [
  {
    id: "drive",
    label: "Google Drive",
    icon: "GD",
    ready: true,
    example: "https://drive.google.com/drive/folders/16VQhcRbCHkzhH2cq8T5DwyhTUBj2BrO4",
    steps: {
      title: "Share a Google Drive folder",
      items: [
        "Right-click your folder, choose Share",
        'Under "General access", set it to "Anyone with the link"',
        "Copy the link, paste it in the box above, then Scan",
      ],
    },
  },
  {
    id: "github",
    label: "GitHub",
    icon: "GH",
    ready: true,
    example: "https://github.com/yargerlab/Data",
    steps: {
      title: "Share a GitHub repository",
      items: [
        "Make the repository public",
        "Copy its URL (or just owner/repo)",
        "Paste it in the box above, then Scan",
      ],
    },
  },
  { id: "dropbox", label: "Dropbox", icon: "DB", ready: false },
  { id: "repos", label: "Zenodo · OSF", icon: "ZO", ready: false },
];

export function ConnectGuide({ onTryExample }: { onTryExample?: (url: string) => void }) {
  const [active, setActive] = useState("drive");
  const provider = PROVIDERS.find((p) => p.id === active) ?? PROVIDERS[0];

  return (
    <div className="connect">
      <div className="connect-head">
        <span className="section-title" style={{ margin: 0 }}>Connect a public data source</span>
        <span className="muted">No account, no API key, no install — just a public share link.</span>
      </div>

      <div className="provider-grid">
        {PROVIDERS.map((p) => (
          <button
            key={p.id}
            className={"provider" + (p.id === active ? " active" : "") + (p.ready ? "" : " soon")}
            onClick={() => p.ready && setActive(p.id)}
            disabled={!p.ready}
          >
            <span className="provider-ic">{p.icon}</span>
            <span className="provider-name">{p.label}</span>
            <span className={"provider-status" + (p.ready ? " ok" : "")}>{p.ready ? "Ready" : "Soon"}</span>
          </button>
        ))}
      </div>

      {provider.steps && (
        <div className="steps">
          <div className="steps-title">{provider.steps.title}</div>
          {provider.steps.items.map((item, i) => (
            <div className="step" key={i}>
              <span className="step-num">{i + 1}</span>
              <span>{item}</span>
            </div>
          ))}
          {provider.example && onTryExample && (
            <button className="btn ghost sm" onClick={() => onTryExample(provider.example!)}>
              Scan an example
            </button>
          )}
        </div>
      )}
    </div>
  );
}
