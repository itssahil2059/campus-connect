# Git-Together API

Base URL (local): http://127.0.0.1:8000
All responses are JSON. The frontend's `api/client.ts` converts snake_case to camelCase.
Every endpoint except signup/verify/login needs the header `Authorization: Token <token>`
(401 without it).

The tables are the overall plan. Sections marked **Contract** are built and
tested: build the frontend against those exactly.

## Auth (Weeks 2–3)
| Method | Path | Purpose |
| --- | --- | --- |
| POST | /api/auth/signup/ | Create account (.edu email only), sends verification email |
| GET | /api/auth/verify/<uid>/<token>/ | Activate account from email link |
| POST | /api/auth/login/ | Returns login token |
| POST | /api/auth/logout/ | Ends session |
| GET | /api/auth/me/ | Current logged-in user |

## Profiles & questionnaire (Weeks 4–5)
| Method | Path | Purpose |
| --- | --- | --- |
| GET / PUT | /api/profiles/me/ | My profile |
| GET | /api/profiles/<id>/ | Another student's profile (includes `user_id`, used for connections and chat) |
| POST | /api/profiles/me/photo/ | Upload profile photo |
| GET | /api/questions/ | Questionnaire questions |
| GET / POST | /api/answers/ | My questionnaire answers |

## Discovery, search, connections (Weeks 6–7)
| Method | Path | Purpose |
| --- | --- | --- |
| GET | /api/discover/ | Suggested students, best match first |
| GET | /api/search/?q=&college=&interest= | Search and filter |
| GET / POST | /api/connections/ | My connections and requests / send a request |
| POST | /api/connections/<id>/accept/ | Accept a request |
| POST | /api/connections/<id>/decline/ | Decline a request |
| DELETE | /api/connections/<id>/ | Cancel my request / remove a connection |
| GET | /api/connections/with/<user_id>/ | My status with one student (profile button) |

### Contract: connections

Connections are private: you only ever see your own. Every connection is shown
from **your** point of view:

```json
{
  "id": 12,
  "status": "connected",
  "user": {
    "id": 5, "username": "bob", "college_name": "TAMUT",
    "graduation_year": 2027, "profile_id": 3
  },
  "created_at": "2026-11-01T10:00:00-05:00",
  "responded_at": "2026-11-01T10:05:00-05:00"
}
```
- `status`: `"connected"` (accepted), `"incoming"` (they asked you, waiting on
  you), or `"outgoing"` (you asked, waiting on them).
- `user` is the **other** person. `profile_id` is null if they haven't set up a
  profile yet. Link to `/profiles/<profile_id>`.
- Declined requests are never revealed. The sender keeps seeing `"outgoing"`
  and can't send a new request (sending again just returns the same row). The
  person who declined no longer sees it.

**GET /api/connections/?status=connected|incoming|outgoing** → `200 [connection, ...]`,
newest first. Without `?status`, returns all three kinds.

**POST /api/connections/** `{"user_id": 5}`
- `201` + connection (`"outgoing"`): new request sent.
- `200` + connection: nothing new was created. Either you'd already asked, you
  were already connected, or **they had already asked you, so this accepts it**
  (`"connected"`).
- `400 {"user_id": ["..."]}`: yourself, or no such verified student.

**POST /api/connections/<id>/accept/** → `200` + connection (`"connected"`).
`400` if it isn't a pending request sent to you.

**POST /api/connections/<id>/decline/** → `204`. `400` if it isn't a pending
request sent to you.

**DELETE /api/connections/<id>/** → `204`. Cancels your outgoing request, or
removes a connection (either person can). `400` if it's a request sent *to*
you (use decline instead).

**GET /api/connections/with/<user_id>/** → `200 {"status": "none" | "connected" | "incoming" | "outgoing", "connection": connection | null}`.
Use this on a profile page to pick the button: Connect / Requested (cancel) /
Accept + Decline / Connected (Message).

Any connection id that isn't yours → `404`.

## Messaging (Week 8)
| Method | Path | Purpose |
| --- | --- | --- |
| GET | /api/conversations/ | My chats |
| GET | /api/conversations/<id>/messages/ | Chat history |
| WebSocket | /ws/chat/<id>/ | Live messages |
