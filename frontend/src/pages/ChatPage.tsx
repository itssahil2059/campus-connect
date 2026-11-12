
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { apiGet, apiPost, errorMessage } from "../api/client";

type StudentInfo = {
  id: number | string;
  name?: string;
  college?: string;
};

type Message = {
  id: number | string;
  mine: boolean;
  text: string;
  sentAt: string;
};

type ChatLocationState = {
  student?: StudentInfo;
};

type ThemeName =
  | "lavender"
  | "sage"
  | "blue"
  | "peach"
  | "midnight";

const themes: Record<
  ThemeName,
  {
    name: string;
    emoji: string;
    page: string;
    header: string;
    card: string;
    received: string;
    sent: string;
    text: string;
    muted: string;
    border: string;
    button: string;
    input: string;
    accent: string;
  }
> = {
  lavender: {
    name: "Lavender Dream",
    emoji: "✨",
    page: "bg-[#F7F4FC]",
    header: "bg-[#E9E4F7]",
    card: "bg-white",
    received: "bg-[#F0ECF8]",
    sent: "bg-[#DCD2F2]",
    text: "text-[#454052]",
    muted: "text-[#898196]",
    border: "border-[#E7E0F1]",
    button: "bg-[#8975B5] hover:bg-[#76619F]",
    input: "bg-white",
    accent: "text-[#8975B5]",
  },
  sage: {
    name: "Sage Garden",
    emoji: "🌿",
    page: "bg-[#F4F8F3]",
    header: "bg-[#E3EEE5]",
    card: "bg-white",
    received: "bg-[#EDF4ED]",
    sent: "bg-[#D5E7D8]",
    text: "text-[#405347]",
    muted: "text-[#829286]",
    border: "border-[#DCE9DE]",
    button: "bg-[#718D76] hover:bg-[#5E7863]",
    input: "bg-white",
    accent: "text-[#718D76]",
  },
  blue: {
    name: "Cloud Blue",
    emoji: "☁️",
    page: "bg-[#F3F8FC]",
    header: "bg-[#E3EFF8]",
    card: "bg-white",
    received: "bg-[#EDF4FA]",
    sent: "bg-[#D6E8F6]",
    text: "text-[#405366]",
    muted: "text-[#8295A7]",
    border: "border-[#DCEAF4]",
    button: "bg-[#7198B9] hover:bg-[#5D83A4]",
    input: "bg-white",
    accent: "text-[#7198B9]",
  },
  peach: {
    name: "Peachy",
    emoji: "🍑",
    page: "bg-[#FFF8F2]",
    header: "bg-[#FFF0DF]",
    card: "bg-white",
    received: "bg-[#FFF3E8]",
    sent: "bg-[#F9E1CB]",
    text: "text-[#59483E]",
    muted: "text-[#A18A7B]",
    border: "border-[#F3E5D8]",
    button: "bg-[#C58D65] hover:bg-[#AE7750]",
    input: "bg-white",
    accent: "text-[#C58D65]",
  },
  midnight: {
    name: "Midnight",
    emoji: "🌙",
    page: "bg-[#20212B]",
    header: "bg-[#30313F]",
    card: "bg-[#292A36]",
    received: "bg-[#393A49]",
    sent: "bg-[#55516F]",
    text: "text-[#F1EFF8]",
    muted: "text-[#AAA8BC]",
    border: "border-[#414252]",
    button: "bg-[#8176A9] hover:bg-[#716696]",
    input: "bg-[#353644]",
    accent: "text-[#B7A9E0]",
  },
};

// Each conversation gets its own saved theme.
const getSavedTheme = (
  chatId: string | undefined
): ThemeName => {
  if (!chatId) return "lavender";

  try {
    const saved = localStorage.getItem(
      `git-together-chat-theme-${chatId}`
    );

    if (saved && saved in themes) {
      return saved as ThemeName;
    }
  } catch {
    // Use the default theme if storage is unavailable.
  }

  return "lavender";
};

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const locationState = location.state as ChatLocationState | null;
  const student = locationState?.student;

  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const [themeName, setThemeName] = useState<ThemeName>(() =>
    getSavedTheme(id)
  );

  const bottomRef = useRef<HTMLDivElement>(null);

  const theme = themes[themeName];

  // Load the saved theme whenever the conversation changes.
  useEffect(() => {
    setThemeName(getSavedTheme(id));
  }, [id]);

  // Save the theme for this conversation only.
  const changeTheme = (nextTheme: ThemeName) => {
    setThemeName(nextTheme);

    if (!id) return;

    try {
      localStorage.setItem(
        `git-together-chat-theme-${id}`,
        nextTheme
      );
    } catch {
      // The theme still changes for the current session.
    }
  };

  const loadMessages = useCallback(async () => {
    if (!id) return;

    try {
      const response = await apiGet<unknown>(
        `/api/messages/${id}/`
      );

      const rawMessages = Array.isArray(response)
        ? response
        : [];

      const formattedMessages: Message[] = rawMessages.map(
        (item: Record<string, unknown>) => ({
          id: (item.id as number | string) ?? Math.random(),
          mine: Boolean(item.mine ?? item.fromMe),
          text: String(item.text ?? item.body ?? ""),
          sentAt: String(item.sentAt ?? item.createdAt ?? ""),
        })
      );

      setMessages(formattedMessages);
      setError("");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    setLoading(true);
    setMessages([]);
    setError("");

    loadMessages();

    const interval = window.setInterval(() => {
      loadMessages();
    }, 5000);

    return () => window.clearInterval(interval);
  }, [loadMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  const handleSend = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    const trimmedMessage = newMessage.trim();

    if (!trimmedMessage || !id || sending) return;

    const temporaryId = `temp-${Date.now()}`;

    const optimisticMessage: Message = {
      id: temporaryId,
      mine: true,
      text: trimmedMessage,
      sentAt: new Date().toISOString(),
    };

    setMessages((previous) => [
      ...previous,
      optimisticMessage,
    ]);

    setNewMessage("");
    setSending(true);
    setError("");

    try {
      await apiPost(`/api/messages/${id}/`, {
        text: trimmedMessage,
      });

      await loadMessages();
    } catch (err) {
      setMessages((previous) =>
        previous.filter(
          (message) => message.id !== temporaryId
        )
      );

      setNewMessage(trimmedMessage);
      setError(errorMessage(err));
    } finally {
      setSending(false);
    }
  };

  const displayName = student?.name || "Your Chat";

  const formatTime = (date: string) => {
    if (!date) return "";

    const parsedDate = new Date(date);

    if (Number.isNaN(parsedDate.getTime())) return "";

    return parsedDate.toLocaleTimeString([], {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  return (
    <div
      className={`min-h-screen ${theme.page} ${theme.text} transition-colors duration-300`}
    >
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-3 py-5 sm:px-6">

        {/* Header */}
        <header
          className={`mb-4 flex flex-wrap items-center justify-between gap-4 rounded-3xl ${theme.header} p-4 shadow-sm`}
        >
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate("/messages")}
              className={`rounded-full ${theme.card} ${theme.text} px-3 py-2 text-sm shadow-sm transition hover:scale-105`}
            >
              ← Back
            </button>

            <div>
              <h1 className="text-xl font-bold sm:text-2xl">
                {displayName}
              </h1>

              <p className={`text-sm ${theme.muted}`}>
                {student?.college || "Your conversations"} · Chat together
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => navigate("/messages")}
            className={`rounded-full ${theme.card} ${theme.text} px-4 py-2 text-sm font-semibold shadow-sm transition hover:scale-105`}
          >
            All Messages
          </button>
        </header>

        {/* Theme selector */}
        <section
          className={`mb-4 rounded-3xl ${theme.card} border ${theme.border} p-4 shadow-sm`}
        >
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="font-bold">
                Make this chat yours ✨
              </h2>

              <p className={`text-xs ${theme.muted}`}>
                Choose a theme for this conversation.
              </p>
            </div>

            <span className="text-xl">🎨</span>
          </div>

          <div className="flex flex-wrap gap-2">
            {(Object.keys(themes) as ThemeName[]).map(
              (key) => {
                const option = themes[key];
                const selected = themeName === key;

                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => changeTheme(key)}
                    aria-pressed={selected}
                    className={`rounded-full border px-3 py-2 text-xs font-semibold transition hover:scale-105 ${
                      selected
                        ? `${theme.button} border-transparent text-white shadow-sm`
                        : `${theme.page} ${theme.text} ${theme.border}`
                    }`}
                  >
                    {option.emoji} {option.name}
                    {selected && " ✓"}
                  </button>
                );
              }
            )}
          </div>
        </section>

        {/* Chat window */}
        <main
          className={`flex min-h-[480px] flex-1 flex-col overflow-hidden rounded-3xl border ${theme.border} ${theme.card} shadow-sm`}
        >
          <div
            className={`flex items-center justify-between border-b ${theme.border} px-5 py-4`}
          >
            <div>
              <h2 className="font-bold">
                Your Conversation
              </h2>

              <p className={`text-xs ${theme.muted}`}>
                A little space to catch up 💬
              </p>
            </div>

            <span className="text-2xl">✦</span>
          </div>

          {/* Messages */}
          <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
            {loading && (
              <div className={`py-12 text-center ${theme.muted}`}>
                <div className="mb-3 animate-pulse text-3xl">
                  💬
                </div>
                Loading your conversation...
              </div>
            )}

            {!loading && messages.length === 0 && (
              <div className="flex min-h-[300px] flex-col items-center justify-center text-center">
                <div className="mb-4 text-6xl">☁️</div>

                <h3 className="text-lg font-bold">
                  It's a little quiet here!
                </h3>

                <p className={`mt-2 max-w-xs text-sm ${theme.muted}`}>
                  Send the first message and start getting to know each
                  other.
                </p>

                <span className="mt-4 text-2xl">✧</span>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.mine ? "justify-end" : "justify-start"
                }`}
              >
                <div className="max-w-[85%] sm:max-w-[70%]">
                  <div
                    className={`rounded-3xl px-4 py-3 shadow-sm ${
                      message.mine
                        ? `${theme.sent} rounded-br-md`
                        : `${theme.received} rounded-bl-md`
                    }`}
                  >
                    <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                      {message.text}
                    </p>
                  </div>

                  <p
                    className={`mt-1 px-2 text-[10px] ${theme.muted} ${
                      message.mine ? "text-right" : "text-left"
                    }`}
                  >
                    {message.mine ? "You" : displayName}
                    {message.sentAt
                      ? ` · ${formatTime(message.sentAt)}`
                      : ""}
                  </p>
                </div>
              </div>
            ))}

            <div ref={bottomRef} />
          </div>

          {/* Error message */}
          {error && (
            <div className="mx-4 mb-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Message input */}
          <form
            onSubmit={handleSend}
            className={`border-t ${theme.border} p-4`}
          >
            <div
              className={`flex items-center gap-2 rounded-full border ${theme.border} ${theme.input} p-2`}
            >
              <input
                type="text"
                value={newMessage}
                onChange={(event) =>
                  setNewMessage(event.target.value)
                }
                placeholder="Write something nice..."
                className={`min-w-0 flex-1 bg-transparent px-3 py-2 text-sm outline-none ${theme.text}`}
                disabled={sending}
              />

              <button
                type="submit"
                disabled={!newMessage.trim() || sending}
                className={`rounded-full ${theme.button} px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:scale-105 disabled:cursor-not-allowed disabled:opacity-50`}
              >
                {sending ? "Sending..." : "Send ✨"}
              </button>
            </div>

            <p className={`mt-2 text-center text-xs ${theme.muted}`}>
              Be kind, be yourself, and enjoy the conversation ♡
            </p>
          </form>
        </main>
      </div>
    </div>
  );
}
