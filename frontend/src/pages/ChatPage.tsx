import { useLayoutEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { Link, useParams } from "react-router-dom";
import type { Message } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { useChat, type ChatMode } from "../chat/useChat";
import { Alert, Avatar, Button, Spinner, shortTime } from "../components/ui";

const MAX_LENGTH = 2000;

/** /messages/:id. The key makes switching chats start from a clean slate. */
export default function ChatPage() {
  const { id } = useParams();
  const { user } = useAuth();
  if (!user) return null;
  return <ChatView key={id} conversationId={Number(id)} myId={user.id} />;
}

function ChatView({ conversationId, myId }: { conversationId: number; myId: number }) {
  const { conversation, messages, hasOlder, mode, error, sendError, loadOlder, send } = useChat(
    conversationId,
    myId
  );
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingOlder, setLoadingOlder] = useState(false);

  const listRef = useRef<HTMLDivElement>(null);
  const atBottomRef = useRef(true);
  const keepOffsetRef = useRef<number | null>(null);
  const newest = messages.at(-1);
  const oldestId = messages[0]?.id;

  // New message at the bottom: follow it if I'm reading the latest or sent it.
  useLayoutEffect(() => {
    const el = listRef.current;
    if (el && (atBottomRef.current || newest?.senderId === myId)) el.scrollTop = el.scrollHeight;
  }, [newest?.id, newest?.senderId, myId]);

  // Older messages added at the top: keep what I was looking at in place.
  useLayoutEffect(() => {
    const el = listRef.current;
    if (el && keepOffsetRef.current !== null) {
      el.scrollTop = el.scrollHeight - keepOffsetRef.current;
      keepOffsetRef.current = null;
    }
  }, [oldestId]);

  async function handleLoadOlder() {
    const el = listRef.current;
    if (el) keepOffsetRef.current = el.scrollHeight - el.scrollTop;
    setLoadingOlder(true);
    await loadOlder();
    setLoadingOlder(false);
  }

  async function handleSend(e?: FormEvent) {
    e?.preventDefault();
    const body = draft.trim();
    if (!body || sending) return;
    setSending(true);
    if (await send(body)) setDraft("");
    setSending(false);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter adds a new line.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  if (error) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <BackLink />
        <Alert>{error}</Alert>
      </div>
    );
  }
  if (!conversation) {
    return (
      <div className="flex justify-center py-20">
        <Spinner />
      </div>
    );
  }

  const other = conversation.otherUser;
  // "Seen" goes under my latest message once they've read it.
  const lastMine = [...messages].reverse().find((m) => m.senderId === myId);

  return (
    <div className="mx-auto flex h-[calc(100vh-9rem)] max-w-2xl flex-col sm:h-[calc(100vh-11rem)]">
      <BackLink />

      <header className="mt-3 flex items-center gap-3 rounded-t-3xl border border-line bg-white px-4 py-3">
        <Avatar name={other.username} src={other.thumbnailUrl} />
        <div className="min-w-0 flex-1">
          {other.profileId ? (
            <Link to={`/profile/${other.profileId}`} className="font-semibold hover:text-accent-dark">
              {other.username}
            </Link>
          ) : (
            <p className="font-semibold">{other.username}</p>
          )}
          <p className="truncate text-xs text-muted">{other.collegeName}</p>
        </div>
        <ModeBadge mode={mode} />
      </header>

      <div
        ref={listRef}
        onScroll={(e) => {
          const el = e.currentTarget;
          atBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
        }}
        data-testid="message-list"
        className="flex-1 space-y-2 overflow-y-auto border-x border-line bg-cream/40 px-4 py-4"
      >
        {hasOlder && (
          <div className="flex justify-center pb-2">
            <Button variant="ghost" onClick={handleLoadOlder} loading={loadingOlder}>
              Load older messages
            </Button>
          </div>
        )}
        {messages.length === 0 && (
          <p className="py-16 text-center text-sm text-muted">No messages yet. Say hi to {other.username}!</p>
        )}
        {messages.map((m) => (
          <Bubble key={m.id} message={m} mine={m.senderId === myId} seen={m === lastMine && !!m.readAt} />
        ))}
      </div>

      <form onSubmit={handleSend} className="rounded-b-3xl border border-line bg-white p-3">
        {sendError && <p className="mb-2 px-1 text-sm text-accent-dark" role="alert">{sendError}</p>}
        {conversation.isConnected ? (
          <div className="flex items-end gap-2">
            <textarea
              name="message"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              maxLength={MAX_LENGTH}
              rows={1}
              placeholder={`Message ${other.username}…`}
              className="max-h-32 min-h-[2.75rem] flex-1 resize-none rounded-2xl border border-line px-4 py-2.5 text-sm outline-none focus:border-ink focus:ring-2 focus:ring-ink/10"
            />
            <Button type="submit" loading={sending} disabled={!draft.trim()}>
              Send
            </Button>
          </div>
        ) : (
          <p className="px-1 py-2 text-center text-sm text-muted">
            You're no longer connected with {other.username}, so you can't send new messages.
          </p>
        )}
      </form>
    </div>
  );
}

function Bubble({ message, mine, seen }: { message: Message; mine: boolean; seen: boolean }) {
  return (
    <div className={`flex flex-col ${mine ? "items-end" : "items-start"}`} data-testid="message">
      <div
        className={`max-w-[80%] whitespace-pre-wrap break-words rounded-2xl px-4 py-2 text-sm ${
          mine ? "rounded-br-md bg-ink text-cream" : "rounded-bl-md border border-line bg-white"
        }`}
      >
        {message.body}
      </div>
      <span className="mt-0.5 px-1 text-[11px] text-muted">
        {shortTime(message.createdAt)}
        {seen && " · Seen"}
      </span>
    </div>
  );
}

function ModeBadge({ mode }: { mode: ChatMode }) {
  const label = { live: "Live", polling: "Reconnecting…", connecting: "Connecting…" }[mode];
  const dot = mode === "live" ? "bg-emerald-500" : "bg-amber-400";
  return (
    <span className="flex items-center gap-1.5 text-xs text-muted" data-testid="chat-mode" data-mode={mode}>
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {label}
    </span>
  );
}

function BackLink() {
  return (
    <Link to="/messages" className="text-sm text-muted hover:text-ink">
      ← All messages
    </Link>
  );
}
