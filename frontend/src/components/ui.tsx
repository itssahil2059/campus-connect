/* eslint-disable react-refresh/only-export-components */
// Small shared building blocks so every page looks consistent.
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export function Button({
  variant = "primary",
  loading = false,
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost";
  loading?: boolean;
}) {
  const styles =
    variant === "primary"
      ? "bg-ink text-cream hover:bg-ink/85"
      : "bg-transparent text-ink hover:bg-sand";
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${styles} ${className}`}
    >
      {loading && <Spinner small />}
      {children}
    </button>
  );
}

export function TextField({
  label,
  error,
  hint,
  name,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  name: string;
  error?: string;
  hint?: string;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={name} className="block text-sm font-medium">
        {label}
      </label>
      <input
        id={name}
        name={name}
        {...props}
        aria-invalid={!!error}
        className={`w-full rounded-xl border bg-white px-4 py-2.5 text-sm outline-none transition placeholder:text-muted/60 focus:border-ink focus:ring-2 focus:ring-ink/10 ${
          error ? "border-accent" : "border-line"
        }`}
      />
      {error ? (
        <p className="text-sm text-accent-dark" data-error-for={name}>
          {error}
        </p>
      ) : (
        hint && <p className="text-xs text-muted">{hint}</p>
      )}
    </div>
  );
}

export function Alert({ children }: { children: ReactNode }) {
  return (
    <div role="alert" className="rounded-xl bg-accent-soft px-4 py-3 text-sm text-accent-dark">
      {children}
    </div>
  );
}

export function Spinner({ small = false }: { small?: boolean }) {
  return (
    <span
      aria-label="Loading"
      className={`inline-block animate-spin rounded-full border-2 border-current border-t-transparent ${
        small ? "h-4 w-4" : "h-6 w-6 text-muted"
      }`}
    />
  );
}

export function Chip({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "accent" }) {
  const styles = tone === "accent" ? "bg-accent-soft text-accent-dark" : "bg-sand text-ink/80";
  return <span className={`rounded-full px-3 py-1 text-xs font-medium ${styles}`}>{children}</span>;
}

// Literal class names so Tailwind includes them in the build.
const AVATAR_COLORS = [
  "bg-rose-100 text-rose-700",
  "bg-amber-100 text-amber-700",
  "bg-emerald-100 text-emerald-700",
  "bg-sky-100 text-sky-700",
  "bg-violet-100 text-violet-700",
  "bg-teal-100 text-teal-700",
];

/** Initials in a colored circle; the same name always gets the same color. */
export function Avatar({ name, size = "md" }: { name: string; size?: "md" | "lg" }) {
  const hash = [...name].reduce((sum, ch) => sum + ch.charCodeAt(0), 0);
  const color = AVATAR_COLORS[hash % AVATAR_COLORS.length];
  const sizes = size === "lg" ? "h-20 w-20 text-2xl" : "h-12 w-12 text-base";
  return (
    <div
      className={`flex shrink-0 items-center justify-center rounded-full font-display font-semibold ${sizes} ${color}`}
    >
      {name.slice(0, 2).toUpperCase()}
    </div>
  );
}

export function classYear(year: number | null) {
  return year ? `Class of ${year}` : null;
}
