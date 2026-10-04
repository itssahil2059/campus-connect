import { useState, type KeyboardEvent } from "react";

const MAX_TAGS = 15; // matches the backend limit

/** Type a word and press Enter (or comma) to add it as a tag. */
export default function TagInput({
  label,
  name,
  value,
  onChange,
  placeholder,
  error,
}: {
  label: string;
  name: string;
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  error?: string;
}) {
  const [draft, setDraft] = useState("");

  function add(raw: string) {
    const tag = raw.trim().toLowerCase();
    if (tag && !value.includes(tag) && value.length < MAX_TAGS) onChange([...value, tag]);
    setDraft("");
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault(); // don't submit the form / type the comma
      add(draft);
    } else if (e.key === "Backspace" && !draft && value.length) {
      onChange(value.slice(0, -1));
    }
  }

  return (
    <div className="space-y-1.5">
      <label htmlFor={name} className="block text-sm font-medium">
        {label}
      </label>
      <div
        className={`flex flex-wrap items-center gap-2 rounded-xl border bg-white px-3 py-2 transition focus-within:border-ink focus-within:ring-2 focus-within:ring-ink/10 ${
          error ? "border-accent" : "border-line"
        }`}
      >
        {value.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 rounded-full bg-sand py-1 pl-3 pr-1.5 text-xs font-medium"
          >
            {tag}
            <button
              type="button"
              onClick={() => onChange(value.filter((t) => t !== tag))}
              className="flex h-4 w-4 items-center justify-center rounded-full text-muted hover:bg-line hover:text-ink"
              aria-label={`Remove ${tag}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          id={name}
          name={name}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => add(draft)}
          placeholder={value.length ? "" : placeholder}
          className="min-w-[8rem] flex-1 bg-transparent py-1 text-sm outline-none placeholder:text-muted/60"
        />
      </div>
      {error ? (
        <p className="text-sm text-accent-dark">{error}</p>
      ) : (
        <p className="text-xs text-muted">Press Enter after each one.</p>
      )}
    </div>
  );
}
