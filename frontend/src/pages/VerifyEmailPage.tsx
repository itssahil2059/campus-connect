import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiGet, errorMessage } from "../api/client";
import AuthShell from "../components/AuthShell";
import { Alert, Spinner } from "../components/ui";

type Status = { state: "loading" } | { state: "done"; message: string } | { state: "error"; message: string };

export default function VerifyEmailPage() {
  const { uid, token } = useParams();
  const [status, setStatus] = useState<Status>({ state: "loading" });
  // React's dev mode runs effects twice; only call the API once.
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;
    apiGet<{ detail: string }>(`/api/auth/verify/${uid}/${token}/`)
      .then((res) => setStatus({ state: "done", message: res.detail }))
      .catch((err) => setStatus({ state: "error", message: errorMessage(err) }));
  }, [uid, token]);

  if (status.state === "loading") {
    return (
      <AuthShell title="Verifying your email…">
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      </AuthShell>
    );
  }

  if (status.state === "error") {
    return (
      <AuthShell title="Link didn't work">
        <Alert>{status.message}</Alert>
        <p className="mt-4 text-sm text-muted">
          Links expire after 3 days and stop working once you've logged in.
        </p>
        <Link to="/login" className="mt-6 block text-center text-sm font-medium underline-offset-4 hover:underline">
          Go to log in
        </Link>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="You're verified 🎉" subtitle={status.message}>
      <Link
        to="/login"
        className="flex w-full items-center justify-center rounded-full bg-ink px-5 py-2.5 text-sm font-medium text-cream transition hover:bg-ink/85"
      >
        Log in
      </Link>
    </AuthShell>
  );
}
