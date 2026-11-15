import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiDelete, apiGet, apiPost, errorMessage } from "../api/client";
import type { Connection, Conversation, MyProfile, PublicProfile } from "../api/types";
import TagInput from "../components/TagInput";
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
/** Wait this long after the last keystroke before searching. */
const SEARCH_DELAY_MS = 300;

type Tab = "discover" | "friends";
type Sub = "suggested" | "everyone" | "search";

type Student = {
  /** Profile id: used for the /profile/:id link. */
  id: number;
  /** User id: the connections and chat APIs need this one, not the profile id. */
  userId: number;
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
    userId: 1,
    name: "maya_patel",
    college: "Texas A&M University",
    classLabel: "Class of 2027",
    bio: "Always building side projects. Looking for people to hike and play board games with.",
    interests: ["Coding", "Hiking", "Board games"],
    match: 75,
  },
  {
    id: 2,
    userId: 2,
    name: "jordan_lee",
    college: "University of Texas at Austin",
    classLabel: "Class of 2028",
    bio: "Pre-med, early-morning runner, and a podcast addict.",
    interests: ["Running", "Cooking", "Podcasts"],
    match: 25,
  },
  {
    id: 3,
    userId: 3,
    name: "sofia_r",
    college: "Rice University",
    classLabel: "Class of 2026",
    bio: "Love live music and weekend art museum trips.",
    interests: ["Music", "Art", "Hiking"],
    match: 50,
  },
];

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
    userId: p.userId,
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

/** Everything the page needs: students, my interests, my connections. */
async function fetchDiscoverData(): Promise<{
  students: Student[];
  myInterests: string[];
  connections: Record<number, Connection>;
}> {
  if (USE_SAMPLE_DATA) {
    const mine = ["Coding", "Hiking", "Music", "Board games"];

    return {
      myInterests: mine,
      students: sampleStudents.map((student) => ({
        ...student,
        match: calcMatch(mine, student.interests),
      })),
      connections: {},
    };
  }

  const [profiles, me, myConnections] = await Promise.all([
    apiGet<PublicProfile[]>("/api/profiles/"),
    apiGet<MyProfile>("/api/profiles/me/"),
    apiGet<Connection[]>("/api/connections/"),
  ]);

  const mine = me.interests ?? [];

  return {
    myInterests: mine,
    students: profiles.map((profile) => fromProfile(profile, mine)),
    // Keyed by the other student's user id.
    connections: Object.fromEntries(myConnections.map((c) => [c.user.id, c])),
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

  // My connections, keyed by the other student's user id. Loaded from the
  // server so friends and sent requests survive a page refresh.
  const [connections, setConnections] = useState<Record<number, Connection>>({});

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const [search, setSearch] = useState("");
  const [college, setCollege] = useState("All");
  const [interestTags, setInterestTags] = useState<string[]>([]);
  const [likeTags, setLikeTags] = useState<string[]>([]);
  const [dislikeTags, setDislikeTags] = useState<string[]>([]);
  // null while the first search is loading.
  const [searchResults, setSearchResults] = useState<Student[] | null>(null);

  // Fetch first, then set state in .then(), so the effect never sets
  // state synchronously (what the react-hooks lint rule checks for).
  const loadData = useCallback(() => {
    fetchDiscoverData()
      .then((data) => {
        setMyInterests(data.myInterests);
        setStudents(data.students);
        setConnections(data.connections);
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // loading starts true, so only Retry needs to reset it.
  function retry() {
    setLoading(true);
    setError("");
    loadData();
  }

  function isFriend(userId: number) {
    return connections[userId]?.status === "connected";
  }

  function isRequested(userId: number) {
    return connections[userId]?.status === "outgoing";
  }

  function forget(userId: number) {
    setConnections((current) => {
      const next = { ...current };
      delete next[userId];
      return next;
    });
  }

  async function handleRemoveFriend(student: Student) {
    const connection = connections[student.userId];
    if (!connection) return;

    const confirmed = window.confirm(
      `Are you sure you want to remove ${student.name} from your friends list?`
    );

    if (!confirmed) return;

    setActionError("");

    try {
      await apiDelete(`/api/connections/${connection.id}/`);
      forget(student.userId);
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  async function handleAddFriend(student: Student) {
    if (connections[student.userId]) return;

    setActionError("");

    try {
      // Sends a request, or accepts theirs if they already asked you.
      const connection = await apiPost<Connection>("/api/connections/", {
        userId: student.userId,
      });

      setConnections((current) => ({
        ...current,
        [student.userId]: connection,
      }));
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  async function openChat(student: Student) {
    setActionError("");

    try {
      // Finds the existing chat with this friend, or starts one.
      const chat = await apiPost<Conversation>("/api/conversations/", {
        userId: student.userId,
      });

      navigate(`/messages/${chat.id}`);
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  const friends = students.filter((student) =>
    isFriend(student.userId)
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

  // Search runs on the server (GET /api/profiles/?q=...&interest=...), so it
  // also covers likes/dislikes and doesn't depend on what this page loaded.
  const isSearching = tab === "discover" && sub === "search";
  useEffect(() => {
    if (!isSearching) return;

    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    if (college !== "All") params.set("college", college);
    interestTags.forEach((tag) => params.append("interest", tag));
    likeTags.forEach((tag) => params.append("like", tag));
    dislikeTags.forEach((tag) => params.append("dislike", tag));

    // Ignore a response that arrives after the filters changed again.
    let stale = false;
    const timer = setTimeout(() => {
      const request = USE_SAMPLE_DATA
        ? Promise.resolve(students)
        : apiGet<PublicProfile[]>(`/api/profiles/?${params}`).then((profiles) =>
            profiles.map((profile) => fromProfile(profile, myInterests))
          );
      request
        .then((results) => {
          if (!stale) setSearchResults([...results].sort((a, b) => b.match - a.match));
        })
        .catch((err) => {
          if (!stale) setActionError(errorMessage(err));
        });
    }, SEARCH_DELAY_MS);

    return () => {
      stale = true;
      clearTimeout(timer);
    };
  }, [isSearching, search, college, interestTags, likeTags, dislikeTags, students, myInterests]);

  function clearSearch() {
    setSearch("");
    setCollege("All");
    setInterestTags([]);
    setLikeTags([]);
    setDislikeTags([]);
  }

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
    const friend = isFriend(student.userId);

    return (
      <StudentCard
        key={student.id}
        student={student}
        myInterests={myInterests}
        isFriend={friend}
        requested={isRequested(student.userId)}
        onAdd={() => handleAddFriend(student)}
        onMessage={() => openChat(student)}
        onRemove={
          friend
            ? () => handleRemoveFriend(student)
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
            onClick={retry}
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
                          placeholder="Search by username, college, or bio..."
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
                          onClick={clearSearch}
                        >
                          Clear
                        </Button>
                      </div>

                      <div className="mt-4 grid gap-4 sm:grid-cols-3">
                        <TagInput label="Has interests" name="search-interest"
                          value={interestTags} onChange={setInterestTags} placeholder="e.g. hiking" />
                        <TagInput label="Likes" name="search-like"
                          value={likeTags} onChange={setLikeTags} placeholder="e.g. coffee" />
                        <TagInput label="Dislikes" name="search-dislike"
                          value={dislikeTags} onChange={setDislikeTags} placeholder="e.g. smoking" />
                      </div>

                      <p className="mt-3 text-xs text-muted">
                        Tags match exactly, and students must have all of
                        them. Results include all students, regardless of
                        their match percentage.
                      </p>
                    </div>

                    {!searchResults ? (
                      <div className="flex justify-center py-12">
                        <Spinner />
                      </div>
                    ) : (
                      <>
                        <p className="mt-4 text-sm text-muted" data-testid="search-count">
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