import { useCallback, useEffect, useRef, useState } from "react";
import { apiGet, apiPost, errorMessage, fieldErrors, fromServer, wsUrl } from "../api/client";
import type { Conversation, Message, MessagePage } from "../api/types";

/** Polling interval while the WebSocket is down. */
const POLL_MS = 3_000;
/** Reconnect delay after a dropped socket; doubles each failure up to the max. */
const RETRY_START_MS = 2_000;
const RETRY_MAX_MS = 30_000;

// Close codes from the backend's ChatConsumer.
const CLOSE_NOT_LOGGED_IN = 4401;
const CLOSE_NOT_IN_CHAT = 4403;

/** "live" = WebSocket open; "polling" = fallback while (re)connecting. */
export type ChatMode = "connecting" | "live" | "polling";

type ServerEvent =
  | { type: "message"; message: Message }
  | { type: "read"; readerId: number; readAt: string }
  | { type: "error"; detail: string };

/**
 * Everything the chat page needs for one conversation.
 *
 * Live updates come over the WebSocket. If it can't connect (network drop,
 * server restart, or a server without WebSocket support), the hook polls
 * `?after=<lastId>` every few seconds and keeps retrying the socket in the
 * background, so the chat always works, just less instantly.
 */
export function useChat(conversationId: number, myId: number) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [hasOlder, setHasOlder] = useState(false);
  const [mode, setMode] = useState<ChatMode>("connecting");
  const [error, setError] = useState("");
  const [sendError, setSendError] = useState("");

  const wsRef = useRef<WebSocket | null>(null);
  const lastIdRef = useRef(0);
  const base = `/api/conversations/${conversationId}`;

  /** Adds messages, ignoring ones we already have (ids are unique). */
  const merge = useCallback((incoming: Message[]) => {
    if (!incoming.length) return;
    lastIdRef.current = Math.max(lastIdRef.current, ...incoming.map((m) => m.id));
    setMessages((prev) => {
      const byId = new Map(prev.map((m) => [m.id, m]));
      for (const m of incoming) byId.set(m.id, m);
      return [...byId.values()].sort((a, b) => a.id - b.id);
    });
  }, []);

  /** Tells the server I've seen their messages (only if I'm actually looking). */
  const markRead = useCallback(() => {
    if (document.visibilityState !== "visible") return;
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "read" }));
    else apiPost(`${base}/read/`).catch(() => {});
  }, [base]);

  useEffect(() => {
    let stopped = false; // set on unmount, so nothing reconnects afterwards
    let ws: WebSocket | null = null;
    let pollTimer: number | undefined;
    let retryTimer: number | undefined;
    let retryDelay = RETRY_START_MS;

    /** Fetches anything newer than what we have. */
    async function catchUp() {
      const page = await apiGet<MessagePage>(`${base}/messages/?after=${lastIdRef.current}`);
      if (stopped) return;
      merge(page.results);
      if (page.results.some((m) => m.senderId !== myId)) markRead();
    }

    function startPolling() {
      if (pollTimer) return;
      pollTimer = window.setInterval(() => {
        if (document.visibilityState === "visible") catchUp().catch(() => {});
      }, POLL_MS);
    }

    function stopPolling() {
      window.clearInterval(pollTimer);
      pollTimer = undefined;
    }

    function connect() {
      // Browsers can't add an Authorization header to a WebSocket, so the
      // token goes in the URL (the server keeps these URLs out of its logs).
      const token = encodeURIComponent(localStorage.getItem("token") ?? "");
      ws = new WebSocket(wsUrl(`/ws/chat/${conversationId}/?token=${token}`));
      wsRef.current = ws;

      ws.onopen = () => {
        setMode("live");
        retryDelay = RETRY_START_MS;
        stopPolling();
        catchUp().catch(() => {}); // anything sent while we were offline
      };

      ws.onmessage = (event) => {
        const data = fromServer<ServerEvent>(JSON.parse(event.data));
        if (data.type === "message") {
          merge([data.message]);
          if (data.message.senderId !== myId) markRead();
        } else if (data.type === "read" && data.readerId !== myId) {
          // They read the chat: mark my messages as seen.
          setMessages((prev) =>
            prev.map((m) => (m.senderId === myId && !m.readAt ? { ...m, readAt: data.readAt } : m))
          );
        } else if (data.type === "error") {
          setSendError(data.detail);
        }
      };

      ws.onclose = (event) => {
        wsRef.current = null;
        if (stopped) return;
        if (event.code === CLOSE_NOT_LOGGED_IN) {
          setError("Your session has expired. Please log in again.");
          return;
        }
        if (event.code === CLOSE_NOT_IN_CHAT) {
          setError("This chat doesn't exist or isn't yours.");
          return;
        }
        // Dropped or never opened: poll meanwhile, retry with backoff.
        setMode("polling");
        startPolling();
        retryTimer = window.setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, RETRY_MAX_MS);
      };
    }

    // First load: chat details + the latest page, then go live.
    Promise.all([apiGet<Conversation>(`${base}/`), apiGet<MessagePage>(`${base}/messages/`)])
      .then(([conv, page]) => {
        if (stopped) return;
        setConversation(conv);
        merge(page.results);
        setHasOlder(page.hasMore);
        markRead();
        connect();
      })
      .catch((err) => !stopped && setError(errorMessage(err)));

    return () => {
      stopped = true;
      stopPolling();
      window.clearTimeout(retryTimer);
      ws?.close();
      wsRef.current = null;
    };
  }, [base, conversationId, myId, merge, markRead]);

  /** Loads the page of messages before the oldest one shown. */
  const loadOlder = useCallback(async () => {
    const oldest = messages[0]?.id;
    if (!oldest) return;
    try {
      const page = await apiGet<MessagePage>(`${base}/messages/?before=${oldest}`);
      merge(page.results);
      setHasOlder(page.hasMore);
    } catch (err) {
      setSendError(errorMessage(err));
    }
  }, [base, messages, merge]);

  /** Sends over the socket if it's open, otherwise over REST. Returns false on failure. */
  const send = useCallback(
    async (body: string) => {
      setSendError("");
      const ws = wsRef.current;
      if (ws?.readyState === WebSocket.OPEN) {
        // The server echoes it back as a "message" event (with its real id).
        ws.send(JSON.stringify({ type: "message", body }));
        return true;
      }
      try {
        merge([await apiPost<Message>(`${base}/messages/`, { body })]);
        return true;
      } catch (err) {
        setSendError(fieldErrors(err).body ?? errorMessage(err));
        return false;
      }
    },
    [base, merge]
  );

  return { conversation, messages, hasOlder, mode, error, sendError, loadOlder, send };
}
