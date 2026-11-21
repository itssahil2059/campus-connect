import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiDelete, apiGet, apiPost, errorMessage } from "../api/client";
import type { Connection, Conversation, OtherUser } from "../api/types";
import { Alert, Avatar, Button, Spinner, classYear } from "../components/ui";

type Tab = "connections" | "requests";

/** /friends: my connections, and requests waiting on me or on them. */
export default function FriendsPage() {
  const navigate = useNavigate();
  const [all, setAll] = useState<Connection[] | null>(null);
  const [tab, setTab] = useState<Tab>("connections");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiGet<Connection[]>("/api/connections/")
      .then((list) => {
        setAll(list);
        // Land on Requests when someone is waiting for an answer.
        if (list.some((c) => c.status === "incoming")) setTab("requests");
      })
      .catch((err) => setError(errorMessage(err)));
  }, []);

  /** Runs an action for one row; the action returns the row's new value (null = remove it). */
  async function act(id: number, action: () => Promise<Connection | null>) {
    setBusyId(id);
    setError("");
    try {
      const updated = await action();
      setAll((list) =>
        (list ?? []).flatMap((c) => (c.id !== id ? [c] : updated ? [updated] : []))
      );
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId(null);
    }
  }

  const accept = (c: Connection) =>
    act(c.id, () => apiPost<Connection>(`/api/connections/${c.id}/accept/`));
  const decline = (c: Connection) =>
    act(c.id, async () => {
      await apiPost(`/api/connections/${c.id}/decline/`);
      return null;
    });
  const remove = (c: Connection, question: string) => {
    if (!window.confirm(question)) return;
    act(c.id, async () => {
      await apiDelete(`/api/connections/${c.id}/`);
      return null;
    });
  };

  async function message(c: Connection) {
    setBusyId(c.id);
    try {
      const chat = await apiPost<Conversation>("/api/conversations/", { userId: c.user.id });
      navigate(`/messages/${chat.id}`);
    } catch (err) {
      setError(errorMessage(err));
      setBusyId(null);
    }
  }

  const connected = all?.filter((c) => c.status === "connected") ?? [];
  const incoming = all?.filter((c) => c.status === "incoming") ?? [];
  const outgoing = all?.filter((c) => c.status === "outgoing") ?? [];

  const tabClass = (t: Tab) =>
    `rounded-full px-4 py-2 text-sm transition ${
      tab === t ? "bg-ink text-cream" : "text-muted hover:text-ink"
    }`;

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-3xl font-semibold sm:text-4xl">Friends</h1>
      <p className="mt-2 text-muted">Only you can see who you're connected with.</p>

      <div className="mt-6 flex gap-2" role="tablist">
        <button role="tab" className={tabClass("connections")} onClick={() => setTab("connections")}>
          Connections {all && `(${connected.length})`}
        </button>
        <button role="tab" className={tabClass("requests")} onClick={() => setTab("requests")}>
          Requests
          {incoming.length > 0 && (
            <span className="ml-2 rounded-full bg-accent px-2 py-0.5 text-xs text-white">{incoming.length}</span>
          )}
        </button>
      </div>

      <div className="mt-6 space-y-6">
        {error && <Alert>{error}</Alert>}
        {!all && !error && (
          <div className="flex justify-center py-20">
            <Spinner />
          </div>
        )}

        {all && tab === "connections" && (
          <Section empty={connected.length === 0 && <Empty text="No connections yet. Find someone on Home and tap Connect." />}>
            {connected.map((c) => (
              <PersonRow key={c.id} user={c.user} testId="connection-row">
                <Button onClick={() => message(c)} loading={busyId === c.id}>
                  Message
                </Button>
                <Button
                  variant="ghost"
                  disabled={busyId === c.id}
                  onClick={() => remove(c, `Remove ${c.user.username}? You won't be able to message each other.`)}
                >
                  Remove
                </Button>
              </PersonRow>
            ))}
          </Section>
        )}

        {all && tab === "requests" && (
          <>
            <Section title="Waiting for you" empty={incoming.length === 0 && <Empty text="No new requests." />}>
              {incoming.map((c) => (
                <PersonRow key={c.id} user={c.user} testId="incoming-row">
                  <Button onClick={() => accept(c)} loading={busyId === c.id}>
                    Accept
                  </Button>
                  <Button variant="ghost" onClick={() => decline(c)} disabled={busyId === c.id}>
                    Decline
                  </Button>
                </PersonRow>
              ))}
            </Section>
            <Section title="Sent by you" empty={outgoing.length === 0 && <Empty text="No pending requests." />}>
              {outgoing.map((c) => (
                <PersonRow key={c.id} user={c.user} testId="outgoing-row">
                  <Button
                    variant="ghost"
                    disabled={busyId === c.id}
                    onClick={() => remove(c, `Cancel your request to ${c.user.username}?`)}
                  >
                    Cancel
                  </Button>
                </PersonRow>
              ))}
            </Section>
          </>
        )}
      </div>
    </div>
  );
}

function Section({ title, empty, children }: { title?: string; empty: ReactNode; children: ReactNode }) {
  return (
    <section>
      {title && <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">{title}</h2>}
      {empty || <div className="space-y-3">{children}</div>}
    </section>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="rounded-3xl border border-dashed border-line px-6 py-10 text-center text-sm text-muted">
      {text}
    </div>
  );
}

/** One person with their actions on the right. Name links to their profile. */
function PersonRow({ user, testId, children }: { user: OtherUser; testId?: string; children?: ReactNode }) {
  const details = [user.collegeName, classYear(user.graduationYear)].filter(Boolean).join(" · ");
  const name = <span className="truncate font-semibold">{user.username}</span>;
  return (
    <div data-testid={testId} className="flex items-center gap-4 rounded-3xl border border-line bg-white p-4">
      <Avatar name={user.username} src={user.thumbnailUrl} />
      <div className="min-w-0 flex-1">
        {user.profileId ? (
          <Link to={`/profile/${user.profileId}`} className="hover:text-accent-dark">
            {name}
          </Link>
        ) : (
          name
        )}
        {details && <p className="truncate text-sm text-muted">{details}</p>}
      </div>
      <div className="flex shrink-0 gap-1">{children}</div>
    </div>
  );
}
