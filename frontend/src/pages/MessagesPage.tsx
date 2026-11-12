
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet, errorMessage } from "../api/client";

//tester data
const USE_SAMPLE_DATA = false;

type Student = {
  id: number | string;
  username: string;
  name: string;
  college: string;
  interests: string[];
};

type Conversation = {
  id: number | string;
  student: Student;
  lastMessage: string;
  time: string;
  updatedAt?: string;
  unread: number;
};

// ==========================================
// SAME SAMPLE STUDENTS AS DISCOVER PAGE
// ==========================================

const sampleStudents: Student[] = [
  {
    id: 1,
    username: "maya_patel",
    name: "Maya Patel",
    college: "Texas A&M",
    interests: ["Coding", "Hiking", "Board games"],
  },
  {
    id: 2,
    username: "jordan_lee",
    name: "Jordan Lee",
    college: "UT Austin",
    interests: ["Running", "Cooking", "Podcasts"],
  },
  {
    id: 3,
    username: "sofia_r",
    name: "Sofia",
    college: "Rice",
    interests: ["Music", "Art", "Hiking"],
  },
  {
    id: 4,
    username: "ethan_b",
    name: "Ethan",
    college: "Texas A&M",
    interests: ["Gaming", "Soccer", "Coding"],
  },
  {
    id: 5,
    username: "aisha_khan",
    name: "Aisha Khan",
    college: "Houston",
    interests: ["Cooking", "Travel", "Photography"],
  },
];

// Same sample friend IDs as DiscoverPage.
const sampleFriendIds = [1, 3];

// Sample conversations.
const sampleConversations: Conversation[] = [
  {
    id: 1,
    student: sampleStudents[0],
    lastMessage: "Hey! How have you been? 😊",
    time: "10:42 AM",
    unread: 1,
  },
  {
    id: 3,
    student: sampleStudents[2],
    lastMessage: "We should definitely talk again!",
    time: "Yesterday",
    unread: 0,
  },
];

// ==========================================
// REAL API DATA FORMATTING
// ==========================================

function formatConversation(item: any): Conversation | null {
  const person =
    item.student ??
    item.otherUser ??
    item.other_user ??
    item.user ??
    item.participant;

  const studentId =
    person?.id ??
    item.studentId ??
    item.student_id ??
    item.userId ??
    item.user_id;

  if (studentId === undefined || studentId === null) {
    return null;
  }

  const name =
    person?.name ??
    person?.username ??
    item.name ??
    item.username ??
    "Student";

  const lastMessage =
    item.lastMessage ??
    item.last_message ??
    item.latestMessage ??
    item.latest_message;

  const messageText =
    typeof lastMessage === "string"
      ? lastMessage
      : lastMessage?.text ??
        lastMessage?.body ??
        item.lastMessageText ??
        item.last_message_text ??
        "Start a conversation!";

  const updatedAt =
    item.updatedAt ??
    item.updated_at ??
    lastMessage?.createdAt ??
    lastMessage?.created_at ??
    "";

  const date = updatedAt ? new Date(updatedAt) : null;

  let time = "";

  if (date && !Number.isNaN(date.getTime())) {
    const today = new Date();

    time =
      date.toDateString() === today.toDateString()
        ? date.toLocaleTimeString([], {
            hour: "numeric",
            minute: "2-digit",
          })
        : date.toLocaleDateString([], {
            month: "short",
            day: "numeric",
          });
  }

  return {
    id: item.id ?? studentId,
    student: {
      id: studentId,
      username: person?.username ?? "",
      name,
      college: person?.college ?? item.college ?? "",
      interests: person?.interests ?? [],
    },
    lastMessage: String(messageText),
    time,
    updatedAt,
    unread: Number(item.unread ?? item.unreadCount ?? item.unread_count ?? 0),
  };
}

export default function MessagesPage() {
  const navigate = useNavigate();

  const [conversations, setConversations] = useState<Conversation[]>(
    USE_SAMPLE_DATA ? sampleConversations : []
  );

  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("All");
  const [loading, setLoading] = useState(!USE_SAMPLE_DATA);
  const [error, setError] = useState("");

  // ==========================================
  // LOAD REAL CONVERSATIONS WHEN SAMPLE DATA
  // IS TURNED OFF
  // ==========================================

  useEffect(() => {
    if (USE_SAMPLE_DATA) {
      setConversations(sampleConversations);
      setLoading(false);
      return;
    }

    let active = true;

    const loadConversations = async () => {
      setLoading(true);
      setError("");

      try {
        const response = await apiGet<unknown>("/api/messages/");

        let results: any[] = [];

        if (Array.isArray(response)) {
          results = response;
        } else if (response && typeof response === "object") {
          const data = response as {
            results?: any[];
            conversations?: any[];
          };

          results = data.results ?? data.conversations ?? [];
        }

        const formatted = results
          .map(formatConversation)
          .filter(
            (conversation): conversation is Conversation =>
              conversation !== null
          );

        if (active) {
          setConversations(formatted);
        }
      } catch (err) {
        if (active) {
          setError(errorMessage(err));
          setConversations([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadConversations();

    return () => {
      active = false;
    };
  }, []);

  // ==========================================
  // SEARCH AND FILTER
  // ==========================================

  const filteredConversations = useMemo(() => {
    return conversations.filter((conversation) => {
      const searchText = search.toLowerCase().trim();

      const matchesSearch = [
        conversation.student.name,
        conversation.student.username,
        conversation.student.college,
        conversation.lastMessage,
      ]
        .join(" ")
        .toLowerCase()
        .includes(searchText);

      const matchesFilter =
        activeFilter === "All" ||
        (activeFilter === "Unread" && conversation.unread > 0);

      return matchesSearch && matchesFilter;
    });
  }, [conversations, search, activeFilter]);

  // ==========================================
  // OPEN INDIVIDUAL CHAT
  // ==========================================

  const openChat = (student: Student) => {
    navigate(`/messages/${student.id}`, {
      state: {
        student: {
          id: student.id,
          name: student.name,
          college: student.college,
        },
      },
    });
  };

  // ==========================================
  // PAGE
  // ==========================================

  return (
    <div className="min-h-screen bg-[#F7F4FC] px-4 py-8 text-[#454052] sm:px-8">
      <div className="mx-auto max-w-5xl">

        {/* Heading */}
        <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="mb-1 text-sm font-semibold text-[#998BB4]">
              YOUR CONNECTIONS ✨
            </p>

            <h1 className="text-3xl font-bold sm:text-4xl">
              Messages 💬
            </h1>

            <p className="mt-2 text-sm text-[#898196]">
              Pick up where your conversations left off.
            </p>
          </div>

          <button
            type="button"
            onClick={() => navigate("/discover")}
            className="rounded-full bg-white px-5 py-3 text-sm font-semibold text-[#76619F] shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          >
            Discover People +
          </button>
        </div>

        {/* Inbox */}
        <div className="overflow-hidden rounded-3xl border border-[#E7E0F1] bg-white shadow-sm">

          {/* Inbox header */}
          <div className="bg-[#E9E4F7] p-5 sm:p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">
                  Your Inbox
                </h2>

                <p className="mt-1 text-sm text-[#898196]">
                  {conversations.length} conversations
                </p>
              </div>

              <span className="text-3xl">✉️</span>
            </div>

            {/* Search */}
            <div className="mt-5 flex items-center gap-3 rounded-2xl bg-white px-4 py-3">
              <span>🔎</span>

              <input
                type="text"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search your conversations..."
                className="w-full bg-transparent text-sm outline-none placeholder:text-[#AAA2B5]"
              />

              {search && (
                <button
                  type="button"
                  onClick={() => setSearch("")}
                  className="text-sm text-[#898196]"
                  aria-label="Clear search"
                >
                  ✕
                </button>
              )}
            </div>

            {/* Filters */}
            <div className="mt-4 flex gap-2">
              {["All", "Unread"].map((filter) => (
                <button
                  key={filter}
                  type="button"
                  onClick={() => setActiveFilter(filter)}
                  className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                    activeFilter === filter
                      ? "bg-[#8975B5] text-white"
                      : "bg-white text-[#76619F] hover:bg-[#F8F6FC]"
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>

          {/* Conversation list */}
          <div className="p-3 sm:p-5">

            {loading && (
              <div className="py-16 text-center">
                <div className="mb-3 animate-pulse text-4xl">
                  💬
                </div>

                <p className="text-sm text-[#898196]">
                  Loading your messages...
                </p>
              </div>
            )}

            {!loading && error && (
              <div className="rounded-2xl bg-red-50 p-5 text-center">
                <p className="font-semibold text-red-600">
                  Couldn't load your conversations.
                </p>

                <p className="mt-2 text-sm text-red-500">
                  {error}
                </p>

                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="mt-4 rounded-full bg-white px-5 py-2 text-sm font-semibold text-red-600 shadow-sm"
                >
                  Try Again
                </button>
              </div>
            )}

            {!loading &&
              !error &&
              filteredConversations.length > 0 &&
              filteredConversations.map((conversation) => {
                const student = conversation.student;

                return (
                  <button
                    key={conversation.id}
                    type="button"
                    onClick={() => openChat(student)}
                    className="group mb-2 flex w-full items-center gap-4 rounded-2xl border border-transparent p-4 text-left transition hover:border-[#E7E0F1] hover:bg-[#F8F6FC]"
                  >
                    {/* Avatar */}
                    <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#E9E4F7] to-[#DCEAF4] text-xl font-bold text-[#76619F]">
                      {student.name.charAt(0).toUpperCase()}

                      {conversation.unread > 0 && (
                        <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-[#8975B5] px-1 text-xs font-bold text-white">
                          {conversation.unread}
                        </span>
                      )}
                    </div>

                    {/* Student details */}
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h3 className="font-bold text-[#454052] group-hover:text-[#76619F]">
                          {student.name}
                        </h3>

                        <span className="text-xs text-[#AAA2B5]">
                          {conversation.time}
                        </span>
                      </div>

                      {student.college && (
                        <p className="mt-1 text-xs text-[#998BB4]">
                          {student.college}
                        </p>
                      )}

                      <p className="mt-2 truncate text-sm text-[#898196]">
                        {conversation.lastMessage}
                      </p>
                    </div>

                    {/* Open chat */}
                    <span className="text-xl text-[#B7A9CC] transition group-hover:translate-x-1">
                      →
                    </span>
                  </button>
                );
              })}

            {!loading &&
              !error &&
              filteredConversations.length === 0 && (
                <div className="flex flex-col items-center px-4 py-16 text-center">
                  <span className="mb-4 text-5xl">💌</span>

                  <h3 className="text-xl font-bold">
                    {search
                      ? "No conversations found"
                      : activeFilter === "Unread"
                        ? "You're all caught up!"
                        : "Your inbox is waiting!"}
                  </h3>

                  <p className="mt-2 max-w-sm text-sm text-[#898196]">
                    {search
                      ? "Try another search."
                      : activeFilter === "Unread"
                        ? "There are no unread conversations right now."
                        : "Find someone interesting and start a conversation!"}
                  </p>

                  {!search && activeFilter === "All" && (
                    <button
                      type="button"
                      onClick={() => navigate("/discover")}
                      className="mt-5 rounded-full bg-[#8975B5] px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#76619F]"
                    >
                      Explore Students ✨
                    </button>
                  )}
                </div>
              )}
          </div>

          {/* Footer */}
          {!loading && !error && conversations.length > 0 && (
            <div className="border-t border-[#EEE9F4] bg-[#FBFAFD] px-5 py-4 text-center">
              <p className="text-xs text-[#AAA2B5]">
                Good conversations start with a hello ♡
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
