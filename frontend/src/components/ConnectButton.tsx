import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiDelete, apiGet, apiPost, errorMessage } from "../api/client";
import type { Connection, ConnectionWith, Conversation } from "../api/types";
import { Button } from "./ui";

/**
 * The connection controls on someone's profile or card. Shows what fits the
 * current state: Connect -> Requested (cancel) -> Accept/Decline -> Message.
 *
 * `initial`: the state, if the parent already loaded it (Discover loads all
 * connections at once), so a page of cards doesn't make one request each.
 * `onChange`: called after every change, so the parent can stay in sync.
 */
export default function ConnectButton({
  userId,
  initial,
  onChange,
}: {
  userId: number;
  initial?: ConnectionWith;
  onChange?: (state: ConnectionWith) => void;
}) {
  const navigate = useNavigate();
  const [state, setState] = useState<ConnectionWith | null>(initial ?? null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const hasInitial = initial !== undefined;

  useEffect(() => {
    if (hasInitial) return;
    apiGet<ConnectionWith>(`/api/connections/with/${userId}/`)
      .then(setState)
      .catch((err) => setError(errorMessage(err)));
  }, [userId, hasInitial]);

  /** Runs an action, then shows the new state (or the error). */
  async function run(action: () => Promise<ConnectionWith>) {
    setBusy(true);
    setError("");
    try {
      const next = await action();
      setState(next);
      onChange?.(next);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const asState = (c: Connection): ConnectionWith => ({ status: c.status, connection: c });
  const none: ConnectionWith = { status: "none", connection: null };

  const connect = () =>
    run(async () => asState(await apiPost<Connection>("/api/connections/", { userId })));
  const accept = (id: number) =>
    run(async () => asState(await apiPost<Connection>(`/api/connections/${id}/accept/`)));
  const decline = (id: number) =>
    run(async () => {
      await apiPost(`/api/connections/${id}/decline/`);
      return none;
    });
  const remove = (id: number, confirmText: string) => {
    if (!window.confirm(confirmText)) return;
    run(async () => {
      await apiDelete(`/api/connections/${id}/`);
      return none;
    });
  };

  async function message() {
    setBusy(true);
    setError("");
    try {
      const chat = await apiPost<Conversation>("/api/conversations/", { userId });
      navigate(`/messages/${chat.id}`);
    } catch (err) {
      setError(errorMessage(err));
      setBusy(false);
    }
  }

  if (!state) return null;
  const id = state.connection?.id;

  return (
    <div className="flex flex-col items-center gap-2 sm:items-end" data-testid="connect-controls">
      <div className="flex flex-wrap justify-center gap-2">
        {state.status === "none" && (
          <Button onClick={connect} loading={busy}>
            Connect
          </Button>
        )}

        {state.status === "outgoing" && id && (
          <>
            <span className="inline-flex items-center rounded-full bg-sand px-4 py-2.5 text-sm font-medium">
              Requested
            </span>
            <Button variant="ghost" onClick={() => remove(id, "Cancel your connection request?")} loading={busy}>
              Cancel
            </Button>
          </>
        )}

        {state.status === "incoming" && id && (
          <>
            <Button onClick={() => accept(id)} loading={busy}>
              Accept request
            </Button>
            <Button variant="ghost" onClick={() => decline(id)} disabled={busy}>
              Decline
            </Button>
          </>
        )}

        {state.status === "connected" && id && (
          <>
            <Button onClick={message} loading={busy}>
              Message
            </Button>
            <Button
              variant="ghost"
              onClick={() => remove(id, "Remove this connection? You won't be able to message each other.")}
              disabled={busy}
            >
              Remove
            </Button>
          </>
        )}
      </div>
      {state.status === "connected" && <p className="text-xs text-muted">✓ Connected</p>}
      {error && <p className="text-sm text-accent-dark">{error}</p>}
    </div>
  );
}
