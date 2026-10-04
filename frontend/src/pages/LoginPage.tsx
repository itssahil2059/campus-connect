import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError, apiGet, apiPost, errorMessage, fieldErrors } from "../api/client";
import type { User } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import AuthShell from "../components/AuthShell";
import { Alert, Button, TextField } from "../components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const from = (useLocation().state as { from?: string } | null)?.from;
  const [form, setForm] = useState({ schoolEmail: "", password: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErrors({});
    setFormError("");
    try {
      const res = await apiPost<{ token: string; user: User }>("/api/auth/login/", form);
      login(res.token, res.user);
      navigate(await nextPage(from));
    } catch (err) {
      setErrors(fieldErrors(err));
      setFormError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in with your school email."
      footer={
        <>
          New here?{" "}
          <Link to="/signup" className="font-medium text-ink underline-offset-4 hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {formError && !Object.keys(errors).length && <Alert>{formError}</Alert>}
        <TextField label="School email" name="schoolEmail" type="email" value={form.schoolEmail}
          onChange={(e) => setForm({ ...form, schoolEmail: e.target.value })}
          error={errors.schoolEmail} placeholder="you@school.edu" autoComplete="email" required />
        <TextField label="Password" name="password" type="password" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          error={errors.password} autoComplete="current-password" required />
        <Button type="submit" loading={submitting} className="w-full">
          Log in
        </Button>
      </form>
    </AuthShell>
  );
}

/** First-time users (no profile yet) go to setup; everyone else to Home. */
async function nextPage(from?: string) {
  try {
    await apiGet("/api/profiles/me/");
    return from ?? "/home";
  } catch (err) {
    return err instanceof ApiError && err.status === 404 ? "/profile/setup" : "/home";
  }
}
