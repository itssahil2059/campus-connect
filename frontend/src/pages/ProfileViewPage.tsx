import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiGet, errorMessage } from "../api/client";
import type { PublicProfile } from "../api/types";
import ConnectButton from "../components/ConnectButton";
import { Alert, Avatar, Chip, Spinner, classYear } from "../components/ui";

/** /profile/:id — one student's full profile. */
export default function ProfileViewPage() {
  const { id } = useParams();
  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<PublicProfile>(`/api/profiles/${id}/`)
      .then(setProfile)
      .catch((err) => setError(errorMessage(err)));
  }, [id]);

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/home" className="text-sm text-muted hover:text-ink">
        ← Back
      </Link>

      {error && <div className="mt-6"><Alert>{error}</Alert></div>}
      {!profile && !error && (
        <div className="flex justify-center py-20">
          <Spinner />
        </div>
      )}

      {profile && (
        <article className="mt-6 rounded-3xl border border-line bg-white p-6 sm:p-10">
          <div className="flex flex-col items-center text-center sm:flex-row sm:items-center sm:gap-6 sm:text-left">
            <Avatar name={profile.username} size="lg" />
            <div className="mt-4 sm:mt-0">
              <h1 className="font-display text-3xl font-semibold">{profile.username}</h1>
              <p className="mt-1 text-muted">
                {[profile.collegeName, classYear(profile.graduationYear)].filter(Boolean).join(" · ")}
              </p>
            </div>
            <div className="mt-6 sm:ml-auto sm:mt-0">
              <ConnectButton userId={profile.userId} />
            </div>
          </div>

          {profile.bio && <p className="mt-8 whitespace-pre-line leading-relaxed text-ink/85">{profile.bio}</p>}

          <TagSection title="Interests" tags={profile.interests} />
          <div className="grid gap-x-8 sm:grid-cols-2">
            <TagSection title="Likes" tags={profile.likes} tone="accent" />
            <TagSection title="Dislikes" tags={profile.dislikes} />
          </div>
        </article>
      )}
    </div>
  );
}

function TagSection({ title, tags, tone }: { title: string; tags: string[]; tone?: "accent" }) {
  if (!tags.length) return null;
  return (
    <section className="mt-8">
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">{title}</h2>
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <Chip key={tag} tone={tone}>
            {tag}
          </Chip>
        ))}
      </div>
    </section>
  );
}
