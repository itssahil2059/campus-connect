import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiGet, apiPost, errorMessage } from "../api/client";
import type { MyProfile, PublicProfile } from "../api/types";
import {
  Alert,
  Avatar,
  Button,
  Chip,
  Spinner,
  classYear,
} from "../components/ui";

const MATCH_THRESHOLD = 20;
const MAX_CHIPS = 4;
const USE_SAMPLE_DATA = false;

type Tab = "discover" | "friends";
type Sub = "suggested" | "everyone" | "search";

type Student = {
  id: number;
  name: string;
  college: string;
  classLabel: string | null;
  bio: string;
  interests: string[];
  match: number;
};

const sampleStudents: Student[] = [
  {
    id: 1,
    name: "maya_patel",
    college: "Texas A&M University",
    classLabel: "Class of 2027",
    bio: "Always building side projects. Looking for people to hike and play board games with.",
    interests: ["Coding", "Hiking", "Board games"],
    match: 75,
  },
  {
    id: 2,
    name: "jordan_lee",
    college: "University of Texas at Austin",
    classLabel: "Class of 2028",
    bio: "Pre-med, early-morning runner, and a podcast addict.",
    interests: ["Running", "Cooking", "Podcasts"],
    match: 25,
  },
  {
    id: 3,
    name: "sofia_r",
    college: "Rice University",
    classLabel: "Class of 2026",
    bio: "Love live music and weekend art museum trips.",
    interests: ["Music", "Art", "Hiking"],
    match: 50,
  },
];

const SAMPLE_FRIEND_IDS = [1, 3];

const OTHER_PAGES = [
  { label: "Feed", to: "/home" },
  { label: "My Profile", to: "/profile/edit" },
  { label: "Questionnaire", to: "/questionnaire" },
];

function calcMatch(mine: string[], theirs: string[]) {
  const a = new Set(mine.map((i) => i.toLowerCase()));
  const b = new Set(theirs.map((i) => i.toLowerCase()));

  const shared = [...a].filter((i) => b.has(i)).length;
  const total = new Set([...a, ...b]).size;

  return total === 0 ? 0 : Math.round((shared / total) * 100);
}

function fromProfile(p: PublicProfile, mine: string[]): Student {
  const interests = p.interests ?? [];

  return {
    id: p.id,
    name: p.username,
    college: p.collegeName ?? "",
    classLabel: p.graduationYear
      ? classYear(p.graduationYear)
      : null,
    bio: p.bio ?? "",
    interests,
    match: calcMatch(mine, interests),
  };
}

/* ---------------- Student Card ---------------- */

function StudentCard({
  student,
  myInterests,
  isFriend,
  requested,
  onAdd,
  onMessage,
  onRemove,
}: {
  student: Student;
  myInterests: string[];
  isFriend: boolean;
  requested: boolean;
  onAdd: () => void;
  onMessage: () => void;
  onRemove?: () => void;
}) {
  const mine = myInterests.map((i) => i.toLowerCase());
  const extra = student.interests.length - MAX_CHIPS;

  return (
    <article className="flex flex-col rounded-3xl border border-line bg-white p-6 transition hover:shadow-md">
      <div className="flex items-center gap-4">
        <Avatar name={student.name} />

        <div className="min-w-0">
          <p className="truncate font-semibold">{student.name}</p>

          <p className="truncate text-sm text-muted">
            {student.college}
          </p>

          {student.classLabel && (
            <p className="text-xs text-muted/80">
              {student.classLabel}
            </p>
          )}
        </div>

        <span className="ml-auto whitespace-nowrap text-sm font-medium text-accent-dark">
          {student.match}% match
        </span>
      </div>

      {student.bio && (
        <p className="mt-4 text-sm text-ink/85">
          {student.bio}
        </p>
      )}

      {student.interests.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {student.interests.slice(0, MAX_CHIPS).map((tag) => (
            <Chip
              key={tag}
              tone={
                mine.includes(tag.toLowerCase())
                  ? "accent"
                  : "neutral"
              }
            >
              {tag}
            </Chip>
          ))}

          {extra > 0 && <Chip>+{extra}</Chip>}
        </div>
      )}

      <div className="mt-auto flex flex-col gap-2 pt-5">
        {isFriend ? (
          <>
            <Button
              type="button"
              onClick={onMessage}
              className="w-full"
            >
              Message
            </Button>

            {onRemove && (
              <button
                type="button"
                onClick={onRemove}
                className="w-full rounded-full border border-red-200 px-5 py-2.5 text-sm font-medium text-red-600 transition hover:bg-red-50"
              >
                Remove Friend
              </button>
            )}
          </>
        ) : (
          <Button
            type="button"
            onClick={onAdd}
            disabled={requested}
            className="w-full"
          >
            {requested ? "Request sent" : "Add friend"}
          </Button>
        )}

        <Link
          to={`/profile/${student.id}`}
          className="flex w-full items-center justify-center rounded-full border border-line px-5 py-2.5 text-sm font-medium text-ink transition hover:bg-sand"
        >
          View profile
        </Link>
      </div>
    </article>
  );
}

/* ---------------- Discover Page ---------------- */

export default function DiscoverPage() {
  const navigate = useNavigate();

  const [tab, setTab] = useState<Tab>("discover");
  const [sub, setSub] = useState<Sub>("suggested");

  const [students, setStudents] = useState<Student[]>([]);
  const [myInterests, setMyInterests] = useState<string[]>([]);

  const [friendIds, setFriendIds] = useState<number[]>(
    USE_SAMPLE_DATA ? SAMPLE_FRIEND_IDS : []
  );

  const [sentRequests, setSentRequests] = useState<number[]>([]);
  const [removedFriendIds, setRemovedFriendIds] = useState<number[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const [search, setSearch] = useState("");
  const [college, setCollege] = useState("All");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      if (USE_SAMPLE_DATA) {
        const mine = ["Coding", "Hiking", "Music", "Board games"];

        setMyInterests(mine);

        setStudents(
          sampleStudents.map((student) => ({
            ...student,
            match: calcMatch(mine, student.interests),
          }))
        );

        setFriendIds(SAMPLE_FRIEND_IDS);
      } else {
        const [profiles, me] = await Promise.all([
          apiGet<PublicProfile[]>("/api/profiles/"),
          apiGet<MyProfile>("/api/profiles/me/"),
        ]);

        const mine = me.interests ?? [];

        setMyInterests(mine);
        setStudents(profiles.map((profile) => fromProfile(profile, mine)));
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  function isFriend(id: number) {
    return (
      !removedFriendIds.includes(id) &&
      friendIds.includes(id)
    );
  }

  function handleRemoveFriend(id: number) {
    const student = students.find((s) => s.id === id);

    const confirmed = window.confirm(
      `Are you sure you want to remove ${
        student?.name ?? "this friend"
      } from your friends list?`
    );

    if (!confirmed) return;

    setRemovedFriendIds((current) =>
      current.includes(id) ? current : [...current, id]
    );

    setFriendIds((current) =>
      current.filter((friendId) => friendId !== id)
    );

    setSentRequests((current) =>
      current.filter((friendId) => friendId !== id)
    );
  }

  async function handleAddFriend(id: number) {
    if (sentRequests.includes(id)) return;

    setActionError("");

    try {
      await apiPost("/api/friends/requests/", {
        toUserId: id,
      });

      setSentRequests((current) =>
        current.includes(id) ? current : [...current, id]
      );
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  function openChat(student: Student) {
    navigate(`/messages/${student.id}`, {
      state: {
        student: {
          id: student.id,
          name: student.name,
          college: student.college,
        },
      },
    });
  }

  const friends = students.filter((student) =>
    isFriend(student.id)
  );

  const colleges = useMemo(
    () => [
      "All",
      ...Array.from(
        new Set(
          students
            .map((student) => student.college)
            .filter(Boolean)
        )
      ).sort(),
    ],
    [students]
  );

  const searchResults = useMemo(() => {
    const query = search.trim().toLowerCase();

    return students
      .filter(
        (student) =>
          college === "All" || student.college === college
      )
      .filter((student) => {
        if (!query) return true;

        return (
          student.name.toLowerCase().includes(query) ||
          student.college.toLowerCase().includes(query) ||
          student.bio.toLowerCase().includes(query) ||
          student.interests.some((interest) =>
            interest.toLowerCase().includes(query)
          )
        );
      })
      .sort((a, b) => b.match - a.match);
  }, [students, search, college]);

  // Suggested includes every student with a match of 20% or higher.
  const suggestions = useMemo(
    () =>
      students
        .filter((student) => student.match >= MATCH_THRESHOLD)
        .sort((a, b) => b.match - a.match),
    [students]
  );

  // Everyone includes all students regardless of match percentage.
  const everyone = useMemo(
    () => [...students].sort((a, b) => b.match - a.match),
    [students]
  );

  function renderCard(student: Student) {
    const friend = isFriend(student.id);

    return (
      <StudentCard
        key={student.id}
        student={student}
        myInterests={myInterests}
        isFriend={friend}
        requested={sentRequests.includes(student.id)}
        onAdd={() => handleAddFriend(student.id)}
        onMessage={() => openChat(student)}
        onRemove={
          friend
            ? () => handleRemoveFriend(student.id)
            : undefined
        }
      />
    );
  }

  const headings: Record<Tab, { title: string; description: string }> = {
    discover: {
      title: "Discover students",
      description: "Meet people who share your interests.",
    },
    friends: {
      title: "Friends",
      description: "View and manage your connections.",
    },
  };

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      {/* Sidebar */}

      <nav className="flex gap-1 overflow-x-auto rounded-3xl bg-ink p-2 text-cream lg:w-56 lg:shrink-0 lg:flex-col lg:self-start lg:p-3">
        {(
          [
            ["discover", "Discover"],
            ["friends", "Friends"],
          ] as [Tab, string][]
        ).map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={`whitespace-nowrap rounded-2xl px-4 py-3 text-left text-sm font-medium transition ${
              tab === key
                ? "bg-cream/15 text-cream"
                : "text-cream/70 hover:bg-cream/10"
            }`}
          >
            {label}
          </button>
        ))}

        {/* Messages opens the separate purple inbox page. */}
        <button
          type="button"
          onClick={() => navigate("/messages")}
          className="whitespace-nowrap rounded-2xl px-4 py-3 text-left text-sm font-medium text-cream/70 transition hover:bg-cream/10 hover:text-cream"
        >
          Messages
        </button>

        <div className="hidden h-px bg-cream/15 lg:block" />

        <p className="hidden px-4 text-xs text-cream/50 lg:block">
          OTHER PAGES
        </p>

        {OTHER_PAGES.map((page) => (
          <Link
            key={page.to}
            to={page.to}
            className="whitespace-nowrap rounded-2xl px-4 py-3 text-sm text-cream/70 transition hover:bg-cream/10 hover:text-cream"
          >
            {page.label}
          </Link>
        ))}
      </nav>

      {/* Main content (a div, since the site layout already has a main) */}

      <div className="min-w-0 flex-1">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="font-display text-3xl font-semibold sm:text-4xl">
              {headings[tab].title}
            </h1>

            <p className="mt-2 text-muted">
              {headings[tab].description}
            </p>
          </div>

          <Button
            type="button"
            variant="ghost"
            onClick={loadData}
            loading={loading}
          >
            Refresh
          </Button>
        </div>

        {actionError && (
          <div className="mt-4">
            <Alert>{actionError}</Alert>
          </div>
        )}

        {error && (
          <div className="mt-4">
            <Alert>{error}</Alert>
          </div>
        )}

        {loading && students.length === 0 ? (
          <div className="flex justify-center py-20">
            <Spinner />
          </div>
        ) : (
          <>
            {/* DISCOVER */}

            {tab === "discover" && (
              <>
                <div className="mt-6 flex gap-5 border-b border-line">
                  {(
                    [
                      ["suggested", "Suggested"],
                      ["everyone", "Everyone"],
                      ["search", "Search"],
                    ] as [Sub, string][]
                  ).map(([key, label]) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setSub(key)}
                      className={`border-b-2 px-3 py-3 text-sm font-medium transition ${
                        sub === key
                          ? "border-ink text-ink"
                          : "border-transparent text-muted hover:text-ink"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                {/* Suggested */}

                {sub === "suggested" && (
                  <>
                    <p className="mt-4 text-sm text-muted">
                      {suggestions.length} suggested students with at
                      least {MATCH_THRESHOLD}% compatibility.
                    </p>

                    {suggestions.length > 0 ? (
                      <div className="mt-5 grid gap-4 md:grid-cols-2">
                        {suggestions.map(renderCard)}
                      </div>
                    ) : (
                      <p className="mt-8 text-center text-muted">
                        No suggested students available right now.
                      </p>
                    )}
                  </>
                )}

                {/* Everyone */}

                {sub === "everyone" && (
                  <>
                    <p className="mt-4 text-sm text-muted">
                      Showing all {everyone.length} students.
                    </p>

                    {everyone.length > 0 ? (
                      <div className="mt-5 grid gap-4 md:grid-cols-2">
                        {everyone.map(renderCard)}
                      </div>
                    ) : (
                      <p className="mt-8 text-center text-muted">
                        No students are available right now.
                      </p>
                    )}
                  </>
                )}

                {/* Search */}

                {sub === "search" && (
                  <>
                    <div className="mt-5 rounded-3xl border border-line bg-white p-4">
                      <label
                        htmlFor="discover-search"
                        className="mb-2 block text-sm font-semibold"
                      >
                        Search all students
                      </label>

                      <div className="flex flex-col gap-3 sm:flex-row">
                        <input
                          id="discover-search"
                          type="text"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                          placeholder="Search by username, college, bio, or interest..."
                          className="w-full rounded-xl border border-line px-4 py-3 text-sm outline-none focus:border-ink"
                        />

                        <select
                          value={college}
                          onChange={(e) => setCollege(e.target.value)}
                          aria-label="Filter by college"
                          className="rounded-xl border border-line px-4 py-3 text-sm"
                        >
                          {colleges.map((c) => (
                            <option key={c} value={c}>
                              {c === "All" ? "All colleges" : c}
                            </option>
                          ))}
                        </select>

                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => {
                            setSearch("");
                            setCollege("All");
                          }}
                        >
                          Clear
                        </Button>
                      </div>

                      <p className="mt-3 text-xs text-muted">
                        Search results include all students, regardless
                        of their match percentage.
                      </p>
                    </div>

                    <p className="mt-4 text-sm text-muted">
                      {searchResults.length}{" "}
                      {searchResults.length === 1 ? "result" : "results"}{" "}
                      found.
                    </p>

                    {searchResults.length > 0 ? (
                      <div className="mt-5 grid gap-4 md:grid-cols-2">
                        {searchResults.map(renderCard)}
                      </div>
                    ) : (
                      <p className="mt-8 text-center text-muted">
                        No students match your search. Try another name,
                        interest, or college.
                      </p>
                    )}
                  </>
                )}
              </>
            )}

            {/* FRIENDS */}

            {tab === "friends" && (
              <>
                <p className="mt-5 text-sm text-muted">
                  {friends.length}{" "}
                  {friends.length === 1 ? "friend" : "friends"}
                </p>

                {friends.length > 0 ? (
                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    {friends.map(renderCard)}
                  </div>
                ) : (
                  <div className="mt-8 rounded-3xl border border-dashed border-line px-6 py-16 text-center">
                    <h2 className="font-display text-xl font-semibold">
                      No friends yet
                    </h2>

                    <p className="mt-2 text-sm text-muted">
                      Visit Discover to connect with other students.
                    </p>

                    <Button
                      type="button"
                      onClick={() => setTab("discover")}
                      className="mt-5"
                    >
                      Discover students
                    </Button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}