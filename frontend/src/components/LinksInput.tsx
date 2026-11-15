const MAX_LINKS = 5; // matches the backend limit

/** A short list of URL fields (LinkedIn, GitHub, portfolio...) with add/remove. */
export default function LinksInput({
  value,
  onChange,
  error,
}: {
  value: string[];
  onChange: (links: string[]) => void;
  error?: string;
}) {
  const rows = value.length ? value : [""];

  function update(i: number, url: string) {
    const next = [...rows];
    next[i] = url;
    onChange(next);
  }

  return (
    <div className="space-y-1.5">
      <label htmlFor="link-0" className="block text-sm font-medium">
        Links
      </label>
      <div className="space-y-2">
        {rows.map((url, i) => (
          <div key={i} className="flex gap-2">
            <input
              id={`link-${i}`}
              name={`link-${i}`}
              type="text"
              inputMode="url"
              value={url}
              onChange={(e) => update(i, e.target.value)}
              placeholder="e.g. linkedin.com/in/yourname"
              className={`flex-1 rounded-xl border bg-white px-4 py-2.5 text-sm outline-none transition placeholder:text-muted/60 focus:border-ink focus:ring-2 focus:ring-ink/10 ${
                error ? "border-accent" : "border-line"
              }`}
            />
            {rows.length > 1 && (
              <button
                type="button"
                onClick={() => onChange(rows.filter((_, j) => j !== i))}
                className="rounded-xl px-3 text-muted hover:bg-sand hover:text-ink"
                aria-label={`Remove link ${i + 1}`}
              >
                ×
              </button>
            )}
          </div>
        ))}
      </div>
      {rows.length < MAX_LINKS && (
        <button
          type="button"
          onClick={() => onChange([...rows, ""])}
          className="text-sm font-medium text-muted hover:text-ink"
        >
          + Add link
        </button>
      )}
      {error ? (
        <p className="text-sm text-accent-dark">{error}</p>
      ) : (
        <p className="text-xs text-muted">Up to {MAX_LINKS}. LinkedIn, GitHub, Instagram, a portfolio…</p>
      )}
    </div>
  );
}
