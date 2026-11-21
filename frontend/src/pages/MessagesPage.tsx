import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet, errorMessage } from "../api/client";
import type { Conversation } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Alert, Avatar, Spinner, shortTime } from "../components/ui";

/** How often the list refreshes (new chats, unread badges). */
const REFRESH_MS = 15_000;

/** /messages: my chats, latest activity first. */
export default function MessagesPage() {
  const { user } = useAuth();
  const [chats, setChats] = useState<Conversation[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = () =>
      apiGet<Conversation[]>("/api/conversations/")
        .then((list) => {
          setChats(list);
          setError("");
        })
        .catch((err) => setError(errorMessage(err)));
    load();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") load();
    }, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-3xl font-semibold sm:text-4xl">Messages</h1>
      <p className="mt-2 text-muted">Private chats with your connections.</p>

      <div className="mt-8 space-y-3">
        {error && <Alert>{error}</Alert>}
        {!chats && !error && (
          <div className="flex justify-center py-20">
            <Spinner />
          </div>
        )}

        {chats?.length === 0 && (
          <div className="rounded-3xl border border-dashed border-line px-6 py-16 text-center">
            <p className="font-display text-xl">No chats yet</p>
            <p className="mt-2 text-sm text-muted">
              Open a connection on the{" "}
              <Link to="/friends" className="text-accent-dark underline">
                Friends
              </Link>{" "}
              page and tap Message.
            </p>
          </div>
        )}

        {chats?.map((chat) => {
          const last = chat.lastMessage;
          const unread = chat.unreadCount > 0;
          const preview = last
            ? `${last.senderId === user?.id ? "You: " : ""}${last.body}`
            : "No messages yet. Say hi!";
          return (
            <Link
              key={chat.id}
              to={`/messages/${chat.id}`}
              data-testid="conversation-row"
              className="flex items-center gap-4 rounded-3xl border border-line bg-white p-4 transition hover:shadow-md"
            >
              <Avatar name={chat.otherUser.username} src={chat.otherUser.thumbnailUrl} />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-3">
                  <p className={`truncate ${unread ? "font-bold" : "font-semibold"}`}>{chat.otherUser.username}</p>
                  {last && <span className="shrink-0 text-xs text-muted">{shortTime(last.createdAt)}</span>}
                </div>
                <div className="flex items-center justify-between gap-3">
                  <p className={`truncate text-sm ${unread ? "font-medium text-ink" : "text-muted"}`}>{preview}</p>
                  {unread && (
                    <span
                      data-testid="unread-badge"
                      className="shrink-0 rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-white"
                    >
                      {chat.unreadCount}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
