import { Link, useLocation } from "react-router-dom";
import AuthShell from "../components/AuthShell";

export default function CheckEmailPage() {
  const email = (useLocation().state as { email?: string } | null)?.email;

  return (
    <AuthShell
      title="Check your inbox"
      subtitle={
        <>
          We sent a verification link to{" "}
          <span className="font-medium text-ink">{email ?? "your school email"}</span>. Click it to
          activate your account.
        </>
      }
      footer={
        <Link to="/login" className="font-medium text-ink underline-offset-4 hover:underline">
          Back to log in
        </Link>
      }
    >
      <div className="flex justify-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-accent-soft text-accent">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-8 w-8">
            <rect x="3" y="5" width="18" height="14" rx="2" />
            <path d="m3 7 9 6 9-6" />
          </svg>
        </div>
      </div>
      {import.meta.env.DEV && (
        <p className="mt-6 rounded-xl bg-sand px-4 py-3 text-xs text-muted">
          Running locally? Emails aren't really sent — the link is printed in the terminal running{" "}
          <code className="font-mono">python manage.py runserver</code>.
        </p>
      )}
    </AuthShell>
  );
}
