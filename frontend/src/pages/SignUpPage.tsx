import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiPost, errorMessage, fieldErrors } from "../api/client";
import AuthShell from "../components/AuthShell";
import { Alert, Button, TextField } from "../components/ui";

const EMPTY = { username: "", schoolEmail: "", collegeName: "", password: "", passwordConfirm: "" };

export default function SignUpPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const update = (field: keyof typeof EMPTY) => (e: { target: { value: string } }) =>
    setForm({ ...form, [field]: e.target.value });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setErrors({});
    setFormError("");
    try {
      await apiPost("/api/auth/signup/", form);
      navigate("/check-email", { state: { email: form.schoolEmail.toLowerCase() } });
    } catch (err) {
      const fields = fieldErrors(err);
      setErrors(fields);
      if (!Object.keys(fields).length) setFormError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Only for students — you'll need your .edu email."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-ink underline-offset-4 hover:underline">
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {formError && <Alert>{formError}</Alert>}
        <TextField label="Username" name="username" value={form.username}
          onChange={update("username")} error={errors.username} autoComplete="username" required />
        <TextField label="School email" name="schoolEmail" type="email" value={form.schoolEmail}
          onChange={update("schoolEmail")} error={errors.schoolEmail}
          placeholder="you@school.edu" autoComplete="email" required />
        <TextField label="College" name="collegeName" value={form.collegeName}
          onChange={update("collegeName")} error={errors.collegeName}
          placeholder="Texas A&M–Texarkana" required />
        <TextField label="Password" name="password" type="password" value={form.password}
          onChange={update("password")} error={errors.password}
          hint="At least 8 characters, not too similar to your email." autoComplete="new-password" required />
        <TextField label="Confirm password" name="passwordConfirm" type="password" value={form.passwordConfirm}
          onChange={update("passwordConfirm")} error={errors.passwordConfirm}
          autoComplete="new-password" required />
        <Button type="submit" loading={submitting} className="w-full">
          Create account
        </Button>
      </form>
    </AuthShell>
  );
}
