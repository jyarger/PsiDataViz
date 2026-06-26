import { useMemo } from "react";
import type { DatasetData } from "../api";

export type TagCategory = "condition" | "instrument" | "chemical";
export interface Tag {
  category: TagCategory;
  value: string;
}
export interface EditableMetadata {
  sample_name: string;
  formula: string;
  smiles: string;
  cas: string;
  instrument: string;
  operator: string;
  date: string;
  time: string;
  solvent: string;
  temperature: string;
  pressure: string;
  notes: string;
  tags: Tag[];
}

const str = (v: unknown): string => (v == null ? "" : String(v));
const first = (m: Record<string, unknown>, ...keys: string[]): string => {
  for (const k of keys) if (m[k] != null) return String(m[k]);
  return "";
};

// Pre-fill the editable metadata from whatever the reader recovered (the universal metadata + the
// technique-specific extras surfaced at the top level, e.g. solvent / temperature_k).
function deriveMetadata(ds: DatasetData): EditableMetadata {
  const m = ds.metadata;
  return {
    sample_name: first(m, "sample_name") || ds.filename,
    formula: first(m, "formula", "molecular_formula"),
    smiles: first(m, "smiles"),
    cas: first(m, "cas", "cas_rn", "cas_registry_no"),
    instrument: first(m, "instrument", "spectrometer"),
    operator: first(m, "operator", "owner"),
    date: first(m, "date"),
    time: first(m, "time"),
    solvent: first(m, "solvent"),
    temperature: first(m, "temperature", "temperature_k"),
    pressure: first(m, "pressure"),
    notes: first(m, "notes"),
    tags: [],
  };
}

const CATEGORY_LABEL: Record<TagCategory, string> = {
  condition: "Condition",
  instrument: "Instrument",
  chemical: "Chemical",
};

// An interactive, session-local metadata editor: review and correct the parsed sample / instrument /
// conditions, and add tags. (Stateless for now — these edits will drive enriched export to CSDM/JCAMP.)
export function MetadataPanel({
  dataset,
  value,
  onChange,
}: {
  dataset: DatasetData;
  value?: EditableMetadata;
  onChange: (m: EditableMetadata) => void;
}) {
  const meta = useMemo(() => value ?? deriveMetadata(dataset), [value, dataset]);
  const set = (patch: Partial<EditableMetadata>) => onChange({ ...meta, ...patch });

  const title = meta.sample_name || dataset.filename;
  return (
    <div className="md-card">
      <div className="md-head">📝 Sample &amp; metadata — {title}</div>
      <div className="md-grid">
        <Field label="Sample name" value={meta.sample_name} onChange={(v) => set({ sample_name: v })} />
        <Field label="Instrument" value={meta.instrument} onChange={(v) => set({ instrument: v })} />
        <Field label="Operator" value={meta.operator} onChange={(v) => set({ operator: v })} />
        <Field label="Date" value={meta.date} onChange={(v) => set({ date: v })} placeholder="YYYY-MM-DD" />
        <Field label="Time" value={meta.time} onChange={(v) => set({ time: v })} />
        <Field label="Solvent" value={meta.solvent} onChange={(v) => set({ solvent: v })} />
        <Field label="Temperature" value={meta.temperature} onChange={(v) => set({ temperature: v })} />
        <Field label="Pressure" value={meta.pressure} onChange={(v) => set({ pressure: v })} />
        <Field label="Formula" value={meta.formula} onChange={(v) => set({ formula: v })} />
        <Field label="SMILES" value={meta.smiles} onChange={(v) => set({ smiles: v })} mono />
        <Field label="CAS no." value={meta.cas} onChange={(v) => set({ cas: v })} />
      </div>
      <label className="md-field md-notes">
        <span>Notes</span>
        <textarea value={meta.notes} onChange={(e) => set({ notes: e.target.value })} rows={2} />
      </label>
      <TagEditor tags={meta.tags} onChange={(tags) => set({ tags })} />
      <div className="md-hint">
        Pre-filled from the file — edit and add tags. These will be embedded when you export the dataset
        (CSDM / JCAMP-DX).
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  mono,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  mono?: boolean;
}) {
  return (
    <label className="md-field">
      <span>{label}</span>
      <input
        className={mono ? "mono" : undefined}
        value={value}
        placeholder={placeholder}
        spellCheck={false}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

function TagEditor({ tags, onChange }: { tags: Tag[]; onChange: (t: Tag[]) => void }) {
  function add(form: HTMLFormElement) {
    const data = new FormData(form);
    const value = String(data.get("value") || "").trim();
    if (!value) return;
    const category = String(data.get("category") || "condition") as TagCategory;
    onChange([...tags, { category, value }]);
    form.reset();
  }
  return (
    <div className="md-tags">
      <div className="md-taglist">
        {tags.length === 0 && <span className="muted">No tags yet</span>}
        {tags.map((t, i) => (
          <span key={i} className={`md-tag md-tag-${t.category}`}>
            <span className="md-tagcat">{CATEGORY_LABEL[t.category]}</span>
            {t.value}
            <button onClick={() => onChange(tags.filter((_, j) => j !== i))} title="Remove">
              ×
            </button>
          </span>
        ))}
      </div>
      <form
        className="md-tagform"
        onSubmit={(e) => {
          e.preventDefault();
          add(e.currentTarget);
        }}
      >
        <select name="category" defaultValue="condition">
          <option value="condition">Condition</option>
          <option value="instrument">Instrument</option>
          <option value="chemical">Chemical</option>
        </select>
        <input name="value" placeholder="Add a tag — e.g. solvent: D2O, 298 K, aspirin" spellCheck={false} />
        <button type="submit">+ Tag</button>
      </form>
    </div>
  );
}
