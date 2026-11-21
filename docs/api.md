# Git-Together API

Base URL (local): http://127.0.0.1:8000
All responses are JSON. The frontend's `api/client.ts` converts snake_case to camelCase.
Every endpoint except signup/verify/resend-verification/login needs the header `Authorization: Token <token>`
(401 without it).

The tables are the overall plan. Sections marked **Contract** are built and
tested: build the frontend against those exactly.

## Auth (Weeks 2–3)
| Method | Path | Purpose |
| --- | --- | --- |
| POST | /api/auth/signup/ | Create account (.edu email only), sends verification email. **503** if the email can't be sent; the account is then not created, so the student can retry |
| POST | /api/auth/resend-verification/ | Body `{"school_email"}`. Sends a new link if that account exists and isn't verified. Always the same 200 answer (doesn't reveal who has an account); 503 if sending fails; 5 per hour per IP (429 after) |
| GET | /api/auth/verify/<uid>/<token>/ | Activate account from email link |
| POST | /api/auth/login/ | Returns login token |
| POST | /api/auth/logout/ | Ends session |
| GET | /api/auth/me/ | Current logged-in user |

## Profiles & questionnaire (Weeks 4–5)
| Method | Path | Purpose |
| --- | --- | --- |
| GET / PUT | /api/profiles/me/ | My profile (`bio`, `date_of_birth` (required, 18+), `gender`, `city`, `interests`, `likes`, `dislikes`, `links`: up to 5 http(s) URLs; read-only `photo_url`, `thumbnail_url`) |
| GET | /api/profiles/<id>/ | A student's profile, including your own (includes `user_id`, used for connections and chat, `age`, never `date_of_birth`, and `photo_url`/`thumbnail_url`) |
| POST / DELETE | /api/profiles/me/photo/ | Upload (multipart) or remove my profile photo (done; see below) |
| GET | /api/questions/ | Questionnaire questions |
| GET / POST | /api/answers/ | My questionnaire answers |

## Discovery, search, connections (Weeks 6–7)
| Method | Path | Purpose |
| --- | --- | --- |
| GET | /api/discover/ | Suggested students, best match first |
| GET | /api/profiles/?q=&college=&city=&gender=&min_age=&max_age=&interest=&like=&dislike= | Search and filter (done; see below) |
| GET / POST | /api/connections/ | My connections and requests / send a request |
| POST | /api/connections/<id>/accept/ | Accept a request |
| POST | /api/connections/<id>/decline/ | Decline a request |
| DELETE | /api/connections/<id>/ | Cancel my request / remove a connection |
| GET | /api/connections/with/<user_id>/ | My status with one student (profile button) |

### Contract: search and filter
Search is the normal profile list with optional query params; they combine
with AND, and blank ones are ignored.

| Param | Matches |
| --- | --- |
| `q` | text in username, college or bio (case-insensitive, partial) |
| `college` | text in college name (case-insensitive, partial) |
| `city` | text in city (case-insensitive, partial) |
| `gender` | exact value: `woman`, `man`, `non_binary`, `other`, `prefer_not_to_say` |
| `min_age`, `max_age` | whole years, inclusive; non-numbers are ignored. Profiles without a date of birth never match an age filter |
| `interest`, `like`, `dislike` | exact tag (case-insensitive); repeat a param to require all, e.g. `?interest=hiking&interest=coding` |

Returns the same list as `GET /api/profiles/` (never yourself, only verified
students).

### Contract: profile photo
One photo per student. The server processes every upload, so clients send
the original file and get back the cleaned-up URLs.

**`POST /api/profiles/me/photo/`**: `multipart/form-data` with one file
field, `photo`. Replaces any existing photo (the old files are deleted).

| Rule | Error (400, `{"photo": ["..."]}`) |
| --- | --- |
| Must be JPEG, PNG, WebP or HEIC, checked by opening it with Pillow (the file name and extension don't count) | "Please upload a JPG, PNG, WebP or HEIC photo." |
| At most 10 MB, checked before the image is decoded | "That photo is too large. The maximum size is 10 MB." |
| At most ~89 million pixels (Pillow's decompression-bomb limit) | "That image is too large to process. Please upload a smaller photo." |
| No file sent | `"No file was submitted."` (DRF's message) |

Also: **400** `{"detail": "Set up your profile before adding a photo."}` if
`PUT /api/profiles/me/` hasn't been done yet. Through Nginx, a request over
10 MB gets **413** before reaching Django.

What gets stored: the photo rotated upright, **all metadata removed**
(EXIF, GPS location, camera details), converted to RGB JPEG, longest side
≤ 1080 px, ~200–300 KB (always < 1 MB); plus a 200×200 center-cropped
thumbnail (~10–20 KB). File names are random UUIDs.

Returns **200** with the full `GET /api/profiles/me/` body.

**`DELETE /api/profiles/me/photo/`**: removes the photo and both files.
Returns **200** with the profile (`photo_url: null`). Doing it with no photo
is fine (still 200). **404** if the profile isn't set up.

There's no user id in these URLs: they always act on the logged-in user's
own profile, so nobody can change another student's photo.

**URLs in responses.** `photo_url` (the ≤ 1080 px photo, for the profile
page) and `thumbnail_url` (200 px, for lists and cards) are in
`/api/profiles/me/`, `/api/profiles/` and `/api/profiles/<id>/`.
Connections and chats include `thumbnail_url` on each `user` / `other_user`.
All are `null` without a photo (show initials). They're paths like
`/media/profile_photos/<uuid>.jpg`, relative to the API host (the frontend's
`mediaUrl()` adds the host in dev); if storage moves to S3 they become full
`https://` URLs, which clients should use as they are.

```json
{ "id": 4, "bio": "...", "photo_url": "/media/profile_photos/3f2a…c1.jpg",
  "thumbnail_url": "/media/profile_photos/thumbs/3f2a…c1_thumb.jpg", "...": "..." }
```

### Contract: connections

Connections are private: you only ever see your own. Every connection is shown
from **your** point of view:

```json
{
  "id": 12,
  "status": "connected",
  "user": {
    "id": 5, "username": "bob", "college_name": "TAMUT",
    "graduation_year": 2027, "profile_id": 3,
    "thumbnail_url": null
  },
  "created_at": "2026-11-01T10:00:00-05:00",
  "responded_at": "2026-11-01T10:05:00-05:00"
}
```
- `status`: `"connected"` (accepted), `"incoming"` (they asked you, waiting on
  you), or `"outgoing"` (you asked, waiting on them).
- `user` is the **other** person. `profile_id` is null if they haven't set up a
  profile yet. Link to `/profiles/<profile_id>`. `thumbnail_url` is their 200 px
  photo, or null (see "Contract: profile photo").
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
| GET / POST | /api/conversations/ | My chats / open a chat with a connection |
| GET | /api/conversations/<id>/ | One chat |
| GET / POST | /api/conversations/<id>/messages/ | Chat history / send a message |
| POST | /api/conversations/<id>/read/ | Mark their messages as read |
| WebSocket | /ws/chat/<id>/?token=<token> | Live messages and read receipts |

### Contract: chat (REST + polling)

You can only start a chat with, or send messages to, an **accepted connection**.
If two people disconnect, the chat stays in both lists and its history stays
readable, but `is_connected` becomes `false` and sending returns 403. Disable
the message box when `is_connected` is false.

**Message:**
```json
{
  "id": 341, "conversation_id": 7, "sender_id": 5, "body": "hey!",
  "created_at": "2026-11-01T10:00:00-05:00", "read_at": null
}
```
Message ids only go up. Use `id` (not `created_at`) for ordering and as the
polling cursor. `sender_id === me.id` means "my bubble". `read_at` is set
when the other person marks the chat read.

**Conversation:**
```json
{
  "id": 7,
  "other_user": {"id": 5, "username": "bob", "college_name": "TAMUT",
                 "graduation_year": 2027, "profile_id": 3, "thumbnail_url": null},
  "last_message": message | null,
  "unread_count": 2,
  "is_connected": true,
  "updated_at": "2026-11-01T10:00:00-05:00"
}
```

**GET /api/conversations/** → `200 [conversation, ...]`, latest activity first.
Use it for the `/messages` page and unread badges.

**POST /api/conversations/** `{"user_id": 5}` → `201` (new) or `200` (already
existed) + conversation. Use it for the "Message" button on a profile or
connection, then navigate to `/messages/<id>`.
- `403`: not connected (a pending request isn't enough)
- `400 {"user_id": [...]}`: yourself or no such user

**GET /api/conversations/<id>/** → `200` conversation (chat page header).

**GET /api/conversations/<id>/messages/** → `200 {"results": [message, ...], "has_more": bool}`,
`results` always **oldest first**, at most 50.
- no params: the latest 50 (open the chat with this)
- `?before=<id>`: the 50 before that id (pass your oldest id when scrolling up).
  `has_more: false` = start of the chat
- `?after=<id>`: messages newer than that id (**polling**: pass your newest
  id). `has_more: true` = more than 50 arrived, so call again with the new
  newest id
- `400` if `after`/`before` isn't a number

**POST /api/conversations/<id>/messages/** `{"body": "hey!"}` → `201` message.
- `400 {"body": [...]}`: blank (whitespace only) or over 2000 characters.
  Leading/trailing spaces are trimmed
- `403`: no longer connected
- `429`: more than 60 messages a minute. Show "Slow down" and retry later

**POST /api/conversations/<id>/read/** → `204`. Marks every message from the
other person as read. Call it when the chat is open and new messages arrive.

A conversation id that isn't yours → `404` on all of the above.

**Polling recipe (fallback if the WebSocket can't connect):**
1. Open `/messages/<id>`: `GET .../messages/`, render, remember `lastId`, then `POST .../read/`.
2. Every 3 s while the page is visible: `GET .../messages/?after=lastId`.
   Append the results, update `lastId`, and `POST .../read/` if any came from the other person.
3. On send: `POST .../messages/` and append the returned message (and update
   `lastId`) right away. The next poll won't return it again because its id ≤ `lastId`.
4. `/messages` list: `GET /api/conversations/` every 10–15 s for unread badges.

### Contract: chat WebSocket (live)

Open one socket per open chat page:

```ts
const proto = location.protocol === "https:" ? "wss" : "ws";
// Production: same host as the page. Local dev: the API host (127.0.0.1:8000).
const ws = new WebSocket(`${proto}://${apiHost}/ws/chat/${conversationId}/?token=${token}`);
```
The token goes in the URL because browsers can't set headers on a
WebSocket. The server keeps these URLs out of its logs.

**Client → server**
| Send | Effect |
| --- | --- |
| `{"type": "message", "body": "hey!"}` | Saves and delivers a message (same rules as `POST .../messages/`) |
| `{"type": "read"}` | Marks the other person's messages read (same as `POST .../read/`) |

**Server → client**
| Receive | Meaning |
| --- | --- |
| `{"type": "message", "message": message}` | A new message, **including your own** (that's your confirmation, with its real `id`). Same message shape as REST |
| `{"type": "read", "reader_id": 5, "read_at": "..."}` | Someone read the chat. If `reader_id` isn't you, mark your sent messages "Seen" |
| `{"type": "error", "detail": "..."}` | Your last message wasn't sent: blank, over 2000 chars, more than 60/min, or no longer connected. Show `detail` |

Messages sent through the REST endpoint are pushed to open sockets too, so
REST and WebSocket can be mixed.

**Close codes** (`ws.onclose = (e) => e.code`)
| Code | Meaning | Do |
| --- | --- | --- |
| 4401 | Missing/invalid token | Send the user to login |
| 4403 | Not your chat (or it doesn't exist) | Show "chat not found" |
| other (1006 etc.) | Network drop / server restart | Reconnect after a few seconds, then `GET .../messages/?after=<lastId>` to catch up on anything missed |

**Recommended page flow**
1. `GET .../messages/` → render → remember `lastId` → open the socket.
2. On `message`: append it if `id > lastId` (this skips duplicates), then update `lastId`.
   If it's from the other person and the tab is visible, send `{"type": "read"}`.
3. Send with `ws.send(JSON.stringify({type: "message", body}))`. Show the
   message once it comes back (or show it greyed out until then).
4. If the socket can't connect, use the polling recipe above instead.
5. The `/messages` list still uses `GET /api/conversations/` (poll every
   10–15 s for unread badges). Sockets are per chat only.
