import { useEffect, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ApiError, apiGet, apiPost, apiPut, errorMessage, fieldErrors } from "../api/client";
import type { Answer, MyProfile, Question } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import LinksInput from "../components/LinksInput";
import TagInput from "../components/TagInput";
import { Alert, Button, Spinner } from "../components/ui";

const BIO_MAX = 500;

/** Used for both /profile/setup (first time) and /profile/edit. */
export default function ProfileFormPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isSetup = useLocation().pathname === "/profile/setup";

  const [loading, setLoading] = useState(true);
  const [bio, setBio] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [likes, setLikes] = useState<string[]>([]);
  const [dislikes, setDislikes] = useState<string[]>([]);
  const [links, setLinks] = useState<string[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  // question id -> chosen option
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  // Load questions, plus the existing profile/answers if there are any.
  useEffect(() => {
    const profile = apiGet<MyProfile>("/api/profiles/me/").catch((err) => {
      if (err instanceof ApiError && err.status === 404) return null; // not set up yet
      throw err;
    });
    Promise.all([profile, apiGet<Question[]>("/api/questions/"), apiGet<Answer[]>("/api/answers/")])
      .then(([p, qs, as]) => {
        if (p) {
          setBio(p.bio);
          setInterests(p.interests);
          setLikes(p.likes);
          setDislikes(p.dislikes);
          setLinks(p.links);
        }
        setQuestions(qs);
        setAnswers(Object.fromEntries(as.map((a) => [a.question, a.choice])));
      })
      .catch((err) => setFormError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setErrors({});
    setFormError("");
    try {
      await apiPut("/api/profiles/me/", {
        bio,
        interests,
        likes,
        dislikes,
        links: links.filter((l) => l.trim()),
      });
      const answerList = Object.entries(answers).map(([question, choice]) => ({
        question: Number(question),
        choice,
      }));
      if (answerList.length) await apiPost("/api/answers/", answerList);
      navigate("/home");
    } catch (err) {
      const fields = fieldErrors(err);
      setErrors(fields);
      setFormError(Object.keys(fields).length ? "Please fix the highlighted fields." : errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-2xl space-y-8">
      <div>
        <h1 className="font-display text-3xl font-semibold">
          {isSetup ? `Nice to meet you, ${user?.username}` : "Edit your profile"}
        </h1>
        <p className="mt-2 text-muted">
          {isSetup
            ? "Tell other students a bit about yourself. You can change this any time."
            : "Update what other students see."}
        </p>
      </div>

      {formError && <Alert>{formError}</Alert>}

      <section className="space-y-5 rounded-3xl border border-line bg-white p-6 sm:p-8">
        <h2 className="font-display text-xl font-semibold">About you</h2>
        <div className="space-y-1.5">
          <label htmlFor="bio" className="block text-sm font-medium">
            Bio
          </label>
          <textarea
            id="bio"
            name="bio"
            rows={4}
            maxLength={BIO_MAX}
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Major, what you're into, what you're looking for on campus…"
            className="w-full resize-none rounded-xl border border-line bg-white px-4 py-3 text-sm outline-none transition placeholder:text-muted/60 focus:border-ink focus:ring-2 focus:ring-ink/10"
          />
          <p className="text-right text-xs text-muted">
            {bio.length}/{BIO_MAX}
          </p>
        </div>
        <TagInput label="Interests" name="interests" value={interests} onChange={setInterests}
          placeholder="e.g. hiking, photography, coding" error={errors.interests} />
        <div className="grid gap-5 sm:grid-cols-2">
          <TagInput label="Likes" name="likes" value={likes} onChange={setLikes}
            placeholder="e.g. tacos, live music" error={errors.likes} />
          <TagInput label="Dislikes" name="dislikes" value={dislikes} onChange={setDislikes}
            placeholder="e.g. 8am classes" error={errors.dislikes} />
        </div>
        <LinksInput value={links} onChange={setLinks} error={errors.links} />
      </section>

      <section className="space-y-6 rounded-3xl border border-line bg-white p-6 sm:p-8">
        <div>
          <h2 className="font-display text-xl font-semibold">Your preferences</h2>
          <p className="mt-1 text-sm text-muted">Pick the answer that fits you best.</p>
        </div>
        {questions.map((q, i) => (
          <fieldset key={q.id} className="space-y-3">
            <legend className="text-sm font-medium">
              <span className="mr-2 text-muted">{i + 1}.</span>
              {q.text}
            </legend>
            <div className="flex flex-wrap gap-2">
              {q.choices.map((choice) => {
                const selected = answers[q.id] === choice;
                return (
                  <button
                    key={choice}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => setAnswers({ ...answers, [q.id]: choice })}
                    className={`rounded-full border px-4 py-2 text-sm transition ${
                      selected
                        ? "border-ink bg-ink text-cream"
                        : "border-line bg-white text-ink hover:border-ink/40"
                    }`}
                  >
                    {choice}
                  </button>
                );
              })}
            </div>
          </fieldset>
        ))}
      </section>

      <div className="flex justify-end gap-3">
        {!isSetup && (
          <Button type="button" variant="ghost" onClick={() => navigate("/home")}>
            Cancel
          </Button>
        )}
        <Button type="submit" loading={saving}>
          {isSetup ? "Finish setup" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}
