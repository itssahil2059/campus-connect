import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, errorMessage } from "../api/client";
import type { PublicProfile } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Alert, Avatar, Chip, Spinner, basicsLine, classYear } from "../components/ui";

const MAX_CHIPS = 4;

/** /home — other verified students' profiles. */
export default function FeedPage() {
  const { user } = useAuth();
  const [profiles, setProfiles] = useState<PublicProfile[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<PublicProfile[]>("/api/profiles/")
      .then(setProfiles)
      .catch((err) => setError(errorMessage(err)));
  }, []);

  return (
    <div>
      <div className="mb-8 sm:mb-10">
        <h1 className="font-display text-3xl font-semibold sm:text-4xl">Hey, {user?.username} 👋</h1>
        <p className="mt-2 text-muted">Verified students on Git Together. Say hi to someone new.</p>
      </div>

      {error && <Alert>{error}</Alert>}
      {!profiles && !error && (
        <div className="flex justify-center py-20">
          <Spinner />
        </div>
      )}

      {profiles?.length === 0 && (
        <div className="rounded-3xl border border-dashed border-line px-6 py-16 text-center">
          <p className="font-display text-xl">No one here yet</p>
          <p className="mt-2 text-sm text-muted">Invite your classmates — profiles show up here once they're verified.</p>
        </div>
      )}

      {!!profiles?.length && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="profile-list">
          {profiles.map((p) => (
            <ProfileCard key={p.id} profile={p} />
          ))}
        </div>
      )}
    </div>
  );
}

function ProfileCard({ profile }: { profile: PublicProfile }) {
  const extra = profile.interests.length - MAX_CHIPS;
  return (
    <Link
      to={`/profile/${profile.id}`}
      data-testid="profile-card"
      className="group flex flex-col rounded-3xl border border-line bg-white p-6 transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-center gap-4">
        <Avatar name={profile.username} src={profile.thumbnailUrl} />
        <div className="min-w-0">
          <p className="truncate font-semibold group-hover:text-accent-dark">{profile.username}</p>
          <p className="truncate text-sm text-muted">{profile.collegeName}</p>
          {profile.graduationYear && (
            <p className="text-xs text-muted/80">{classYear(profile.graduationYear)}</p>
          )}
          {basicsLine(profile) && <p className="text-xs text-muted/80">{basicsLine(profile)}</p>}
        </div>
      </div>
      {profile.bio && <p className="mt-4 line-clamp-3 text-sm text-ink/80">{profile.bio}</p>}
      {profile.interests.length > 0 && (
        <div className="mt-auto flex flex-wrap gap-1.5 pt-5">
          {profile.interests.slice(0, MAX_CHIPS).map((tag) => (
            <Chip key={tag}>{tag}</Chip>
          ))}
          {extra > 0 && <Chip>+{extra}</Chip>}
        </div>
      )}
    </Link>
  );
}
