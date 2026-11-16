# Presentation Notes — Backend (Sahil)

Running log of what was built, why, and what's worth showing in the initial
and final presentations. Updated after each step. Newest work at the bottom
of each section.

---

## 1. Project setup (Sep 17 – Oct 1, 2026)

**What was done**
- Scaffolded the Django backend with a custom user model (`CustomUser`) from
  day one, with fields for school email, college, graduation year, and
  verification flags.
- Local dev environment with **Docker Compose**: PostgreSQL 16 + Redis 7 run
  in containers, so every teammate gets the same database setup with one
  command (`docker compose up -d db redis`).
- Frontend skeleton (Vite + React + TypeScript + Tailwind) with routes and
  placeholder pages for every planned screen.
- Planned API list in `docs/api.md`, written before implementation so the
  frontend and backend agree on endpoints up front.

**Talking points**
- *Why a custom user model at the start?* Django makes it very hard to switch
  to a custom user model after the first migration. Doing it on day one
  avoids a painful rewrite later.
- *Why Docker for the database?* "Works on my machine" problems disappear,
  and the setup mirrors production (AWS RDS for Postgres, ElastiCache for
  Redis).
- *Why write the API list first?* It's a contract between the frontend and
  backend, so both sides can work in parallel.

---

## 2. SA2 — User registration & authentication (in progress, Oct 2026)

### Step (a): Verified the backend runs
- Brought up Postgres + Redis with Docker, ran migrations, started the
  Django server, and confirmed the admin page loads.
- Fixed: Docker Desktop wasn't running; created `backend/.env` from
  `.env.example` (`.env` is never committed, since it holds secrets).

### Step (b): Signup endpoint — `POST /api/auth/signup/`
**What it does**
- Creates an account from username, school email, password (+ confirm),
  college name, graduation year.
- Rejects any email not ending in `.edu` (case-insensitive).
- Rejects duplicate emails, including case variants
  (`SAHIL@tamut.edu` vs `sahil@tamut.edu`).
- Runs Django's password validators (min length, common passwords, too
  similar to username/email, all-numeric).
- Stores emails lowercase and creates the user with **`is_active=False`**, so
  they cannot log in until they verify their email (step c/d).
- Response never includes the password or any password-related field.

**Talking points**
- *Security by default:* new accounts are locked. Django's built-in
  `authenticate()` refuses inactive users, so we get "no login before
  verification" without writing custom login checks.
- *`.edu` restriction* is the core trust feature of the app: only verified
  students can join.
- *Separate `is_active` and `is_edu_verified` flags:* `is_active` = allowed to
  log in (an admin can also use it to ban someone); `is_edu_verified` =
  proved ownership of the school email. Different meanings, kept separate.

**Bug found during testing (good "how we tested" story)**
- Manual testing showed duplicate emails returned Django's generic message
  ("user with this school email already exists.") instead of ours.
- Cause: DRF auto-adds its own uniqueness check from the model's
  `unique=True`, and it runs *before* custom validation. It's also
  case-sensitive.
- Fix: removed DRF's auto check and let our case-insensitive check handle
  all duplicates with one clear message. The database's unique constraint
  still acts as a final safety net.
- Lesson: test the error paths, not just the happy path.

**Manual test results (curl)**
| Test | Expected | Result |
|---|---|---|
| Valid `.edu` signup | 201, user inactive | ✅ |
| `@gmail.com` signup | 400 ".edu" error | ✅ |
| Exact duplicate email | 400 "already exists" | ✅ (after fix) |
| Uppercase duplicate email | 400 "already exists" | ✅ |

**Commit:** `bf05fb9` — Signup: create users inactive and move auth routes to /api/auth/

### Step (c): Email verification link
**What it does**
- After a successful signup, the server emails a link:
  `/api/auth/verify/<uid>/<token>/`.
- `uid` = user id, base64-encoded so it's URL-safe (not secret).
- `token` = Django's `default_token_generator` (the same mechanism Django
  uses for password resets). It's signed with the server's `SECRET_KEY` and
  **nothing is stored in the database**: the server recalculates it to check
  it. It expires after 3 days, or as soon as the user's password or
  last-login time changes.
- Local dev uses Django's **console email backend**, so the email prints in
  the server terminal. Production switches to AWS SES with a single
  `.env` setting and no code changes.

**Talking points**
- *Why not write our own token system?* Django's built-in generator is
  already battle-tested for password resets. Reusing it avoids security
  mistakes and means there's no token table to clean up.
- *Pluggable email backend:* the same code works in dev (console) and prod
  (SES), so we can develop without sending real emails.
- Set `EMAIL_FIELD = "school_email"` on the user model so the token is tied
  to the school email: changing the email invalidates old links. This is a
  class setting, so no database migration was needed.
### Step (d): Verify / login / logout / me
**What it does**
| Endpoint | Access | Result |
|---|---|---|
| `GET /api/auth/verify/<uid>/<token>/` | anyone with the link | Activates the account (`is_active` + `is_edu_verified`) |
| `POST /api/auth/login/` | anyone | School email + password → auth token (active users only) |
| `POST /api/auth/logout/` | logged in | Deletes the token so it stops working immediately |
| `GET /api/auth/me/` | logged in | Returns the current user |

- Uses DRF **token authentication**: the client sends
  `Authorization: Token <key>` on each request. The token is stored
  server-side, so logout truly revokes it (unlike a stateless JWT, which
  stays valid until it expires).

**Talking points (security decisions)**
- *No account enumeration:* "no such email" and "wrong password" return the
  same message, "Invalid email or password." The "please verify your email
  first" hint is only shown when the password is correct.
- *Verification links can't undo a ban:* verify checks `is_edu_verified`,
  not `is_active`, so if an admin deactivates a verified user, an old link
  can't reactivate them.
- *Links stop working after first login:* login updates `last_login`, which
  is part of the token's hash, so the verification link becomes invalid.
- *Correct HTTP status codes:* found that "not logged in" returned `403`
  instead of `401`, because DRF builds the response from the first
  authentication class. Reordering the classes fixed it, so the frontend
  can reliably tell "not logged in" (401) from "not allowed" (403).

**Manual end-to-end test results (curl)**
| Test | Expected | Result |
|---|---|---|
| Login before verifying | 400 "verify your email first" | ✅ |
| Login with wrong password | 400 generic message | ✅ |
| Tampered token / garbage uid | 400 invalid link | ✅ |
| Real verification link | 200 verified | ✅ |
| Same link again | 200 already verified | ✅ |
| Login (any email case) | 200 + token | ✅ |
| `/me/` with token | 200 user data | ✅ |
| `/me/` without token | 401 | ✅ (after fix; was 403) |
| Logout, then `/me/` with old token | 204, then 401 | ✅ |
| Verification link after login | 400 invalid | ✅ |
### Step (e): Automated tests (pytest)
- Added **pytest + pytest-django**. Run with `cd backend && pytest`. Tests use
  a separate throwaway test database, so real data is never touched.
- **Signup: 14 tests**, all passing. They cover: the user is created inactive
  and unverified; the password is stored hashed; no password fields in the
  response; email lowercased; verification email sent; non-.edu emails
  rejected (`gmail.com`, `tamut.edu.com`, `tamut.org`); duplicate email
  rejected in any letter case; password mismatch; password too similar to
  the school email; common password; missing college.
- Found while verifying the password-similarity fix: the similarity
  validator was listed twice in settings, so users saw the same error
  twice. Removed the duplicate and added a **regression test** (a test
  that keeps the bug from coming back).

- **Email verification: 10 tests.** They cover: the full flow (sign up → read
  the link out of the email → verify → log in); an unverified user can't log
  in; a tampered token, another user's token, and garbage uids are all
  rejected; an already-verified user gets "already verified"; an old link
  can't reactivate a banned user; the link stops working after the first
  login.
- Changed the email link to open the **frontend's** `/verify/<uid>/<token>`
  page (set by the `FRONTEND_URL` setting), which then calls the API. The
  user sees a proper page instead of raw JSON.

- **Login / logout / me: 10 tests.** They cover: login returns a 40-character
  token with no password in the response; the email is case-insensitive;
  `last_login` gets recorded; logging in twice reuses the same token; a wrong
  password and an unknown email get the same generic message; `/me/` works
  with a token and returns 401 without one; logout revokes the token
  (afterwards it gets 401); logout itself requires being logged in.
- **Total: 34 API tests, all passing in about 3 seconds.**

**Why token auth instead of sessions:** the React app runs on a different
port (5173) from the API (8000). With a token, the frontend just sends one
`Authorization: Token …` header. Session cookies would need cross-site
cookie and CSRF configuration between the two ports. Tokens are also
stored in the database, so logout revokes them immediately.

**Talking point:** the API tests run in about a second, so they can run
before every commit. Pairing every bug fix with a test is how you keep it
fixed.
### Step (f): Push branch + pull request into `dev`
- `sa2-auth` is pushed to GitHub; the pull request into `dev` is still to open.

---

## 3. SA3 — Profile + preference questionnaire (branch `sa3-profiles`)

**What it does**
- New **`profiles` app**, kept separate from `users`, so login data and
  profile data stay apart.
- **Profile** (one per user): bio, plus interests, likes and dislikes as short
  tag lists. Tags are trimmed, lowercased and de-duplicated; maximum 15
  per list.
- **Questionnaire:** `Question` (text + answer choices) and `Answer` (one per
  user per question, enforced by a database constraint). Five starter
  questions are loaded by a **data migration**, so every teammate's database
  and production get the same questions automatically.

| Endpoint | Purpose |
|---|---|
| `GET / PUT /api/profiles/me/` | My profile. GET returns 404 until it's set up, which tells the frontend to show the setup page. PUT creates or updates it. |
| `GET /api/profiles/` | Home feed: other **verified, active** users who have a profile |
| `GET /api/profiles/<id>/` | One other student's profile |
| `GET /api/questions/` | The questionnaire |
| `GET / POST /api/answers/` | My answers. POST saves a list, replacing earlier answers. |

**Talking points**
- *Privacy:* other users' profiles never include their email. There are two
  serializers: one for "me" and a public one for everyone else.
- *Safety:* the Home feed only shows verified, active users, so unverified
  or banned accounts never appear.
- *All-or-nothing saves:* answers are saved in a database transaction. If
  one answer is invalid, none are saved.
- *Questions live in the database*, not hard-coded, so new questions can be
  added from the admin without changing code.

**Tests: 15 new, 49 total, all passing.** They cover: 404 before setup;
create then update; tag cleanup; tag limit; the feed excludes yourself,
unverified, banned and profile-less users; no email in public profiles;
questions seeded in order; answers saved, replaced, and invalid choices
roll back the whole batch; you only see your own answers; every endpoint
requires login.

---

## 4. Frontend click-through (branch `sa4-frontend-flow`)

**Pages:** Signup → Check your email → Verify → Login → Profile setup
(profile + questionnaire) → Home (cards of other students) → a single
profile view. Built with React + TypeScript + Tailwind; mobile-friendly.

**How it fits together (talking points)**
- *Auth state:* after login the token goes in `localStorage`, and an
  `AuthProvider` makes the current user available to every page. On reload
  it calls `/api/auth/me/` to restore the session, and drops the token if
  it's no longer valid.
- *Protected routes:* `RequireAuth` sends logged-out visitors to `/login`.
- *Smart redirect after login:* first-time users (where `/api/profiles/me/`
  returns 404) go to profile setup; returning users go straight to Home.
- *Server errors shown in the form:* the API's validation messages
  (".edu only", "already exists", weak password) appear right under the
  matching field.
- *Design:* warm neutral palette, one accent color, serif headings, cards
  and tag chips. A placeholder design, to be replaced with the team's UX
  screenshots later.
- `python manage.py seed_demo` adds 6 sample verified students so the Home
  feed isn't empty during demos.

**Bug found during browser testing:** a wrong password showed *no* error on
the login page. The general "Invalid email or password." message was being
treated as a form-field error, which hid the error box. Fixed in the
shared API helper, so every form benefits.

---

## 5. UI automation tests (Selenium) — instructor requirement

- `backend/tests_ui/`: **7 browser tests**, run with `cd backend && pytest tests_ui`
  (add `HEADED=1` in front to watch Chrome click through it live).
- Each run starts its **own** test Django server (on a throwaway test
  database) and its own React dev server pointed at it, then drives real
  Chrome. It never touches real data and doesn't depend on servers you
  already have running.
- Covered: signup rejects non-.edu email; signup rejects a duplicate email
  (any case); **full flow** signup → open the emailed link → verified →
  login → profile setup; wrong password shows an error; unverified user is
  blocked; verified user lands on Home and can log out (token cleared);
  logged-out visitor sent to login.
- **Totals: 49 API tests + 7 UI tests = 56, all passing (about 13 seconds).**

**Talking point:** unit/API tests check each rule quickly. UI tests prove
the real pages, the React code and the API work together, like a user
clicking through. Selenium reads the verification link from the captured
test email, so even the "check your email" step is automated.

---

## 6. Production prep for AWS EC2 (branch `sa5-deploy-prep`)

**What:** made the app ready to run on a real server, without touching AWS yet.
- **Safe-by-default settings:** debug is off unless `.env` turns it on; the
  server refuses to start with the placeholder secret key; every
  environment-specific value comes from `.env`.
- **Production web stack:** Nginx serves the built React app and forwards
  `/api` and `/admin` to **gunicorn**, which runs Django (`runserver` is for
  development only). The frontend and API share one address, so the browser
  makes no cross-origin calls and no CORS setup is needed.
- **Repeatable deploys:** `deploy/setup-server.sh` sets up a fresh Ubuntu
  server once (packages, Node 22, swap, systemd service, Nginx);
  `deploy/deploy.sh` updates the live site in one command (pull, migrate,
  collect static files, build the frontend, restart).
- **Step-by-step AWS guide** in `docs/deploy.md`: budget alert, EC2, Elastic
  IP, RDS (private, reachable only from the server), read-only GitHub deploy
  key, troubleshooting, and teardown.

**How it was tested before spending anything on AWS:** ran gunicorn locally
with production settings behind the **real Nginx config** (in a Docker
container), checked every route (React pages, refresh on deep links,
static files, admin, API 401/404 with no debug-page leak), then clicked the
full signup → verify → login → profile → home flow in Chrome against it.

**Talking point:** "We rehearsed production locally, so the first real
deploy only has to deal with AWS itself, not with app configuration."

---

## 7. First live deploy on AWS (Oct 23–24, 2026)
- **Live at http://18.119.39.20** — EC2 (Ubuntu 24.04) running Nginx +
  gunicorn (systemd service `gittogether`), database on RDS Postgres.
- Deployed commit `b977833` from `dev` with one command:
  `deploy/deploy.sh dev` (pull, install, migrate RDS, collect static, build
  React, restart). Created the admin user and loaded `seed_demo` (6 profiles).
- **Tested end-to-end on the live site:** `.edu` signup → verification link →
  verified → questionnaire → `/home` feed.
- Rebooted the server for security updates; the app came back on its own
  (systemd starts it at boot), so it survives restarts without anyone logging in.

**Known gaps (next steps):** verification emails only print to the server log
(needs AWS SES); HTTP on a bare IP (domain + HTTPS before final submission);
the `/` route is still a placeholder (frontend, Trinity's landing page PR).

**Talking point:** "Because we rehearsed production locally, the real deploy
was one script — the only AWS problems left were AWS ones."
## 7. Connections (branch `sa7-connections`)

**What:** students send connection requests, accept or decline them, and see
their connections. Chat (next) is only allowed between connected students.
New Django app `connections` with one `Connection` model and a DRF viewset.

**Design decisions / talking points:**
- **One row per pair, enforced by the database.** A Postgres unique
  constraint on `LEAST(from_user, to_user), GREATEST(from_user, to_user)`
  makes A→B and B→A the same pair, so duplicate or crossing requests are
  impossible even if two requests arrive at the same instant.
- **Mutual requests auto-accept.** If Bob sends a request to Alice while hers
  to him is pending, they're connected.
- **Rejections are never revealed.** A declined request keeps looking
  "pending" to the sender, and they can't re-send it. That stops request spam
  and spares feelings, which matters on a dating app.
- **Private by design.** Every query is limited to the logged-in user's own
  rows. Anyone else gets 404, not 403, so the API doesn't even confirm a
  connection exists.
- `are_connected(a, b)` helper: one line for chat to check permission.

**Tests:** 25 new pytest tests (model constraints, every endpoint, privacy,
decline/resend rules). Full suite: 74 passing.

---

## 8. Chat Phase A: REST + polling (branch `sa8-chat-rest`)

**What:** private one-to-one chats between connected students, stored in
Postgres. New `chat` app with `Conversation` and `Message` models and a DRF
viewset: chat list with last message and unread count, history, sending, and
read receipts.

**Design decisions / talking points:**
- **Ship polling first, real-time second.** The REST API works on today's
  server with no infrastructure changes. Phase B adds WebSockets on top of the
  same models, so no work is thrown away.
- **One row per pair.** The two users are stored in id order with a unique
  constraint plus a check constraint, so "the chat between Alice and Bob" is
  one row, guaranteed by the database.
- **Cursor pagination by message id** (`?after=` for polling, `?before=` for
  scrolling up). Ids only increase, so one number does both jobs and new
  messages can't shift pages the way offset pagination would.
- **Connections gate sending, not reading.** If two students disconnect,
  history stays but sending is refused (403). That check lives in one
  service function (`send_message`) that the WebSocket will reuse.
- **Fixed query count for the chat list:** unread counts and last message ids
  come from SQL annotations, the last messages load in one bulk query, and
  connection status is one query, so it's no slower with 100 chats than with 1.
- **Rate limit:** 60 messages/min per user (DRF throttling) against spam.

**Gotcha found while testing:** the rate-limit test failed at first because DRF reads
throttle rates once at import time, so overriding settings in a test has no
effect; the test now patches the throttle class.

**Tests:** 25 new tests (models, service rules, every endpoint, privacy, paging,
rate limit). Full suite: 99 passing.

---

## 9. Chat Phase B: real-time WebSockets (branch `sa9-chat-websocket`)

**What:** live chat. Messages and read receipts appear instantly via
WebSockets, using Django Channels + Redis. `ChatConsumer` at
`/ws/chat/<id>/`, with token login middleware and the origin check.

**How it works (good diagram for slides):**
Browser ⇄ WebSocket ⇄ Nginx ⇄ Daphne (ChatConsumer) → saves to Postgres →
publishes to Redis group `chat_<id>` → every open socket in that chat
receives it.

**Design decisions / talking points:**
- **One code path for sending.** REST and WebSocket both call
  `chat.services.send_message`, so the rules are identical, and a message
  sent over REST is pushed live to open sockets too.
- **Token login for WebSockets.** Browsers can't send an Authorization
  header on a WebSocket, so the DRF token goes in the URL. Nginx and Daphne
  access logs are switched off for those URLs so tokens never hit log files.
- **Origin check** (`AllowedHostsOriginValidator`): a malicious site can't
  open a socket to our server from a logged-in student's browser.
- **Meaningful close codes** (4401 not logged in, 4403 not your chat). The
  consumer accepts *then* closes, because closing before accepting hides the
  code from the browser.
- **Best-effort broadcast.** The message is saved first. If Redis is down,
  it's logged and polling still delivers it, so a Redis outage can't lose
  messages.
- **Server change:** gunicorn (sync, HTTP only) was replaced by **Daphne**
  (ASGI: HTTP + WebSockets in one process). Redis runs on the same EC2
  instance and Nginx got a `/ws/` upgrade block, so there's no extra AWS
  cost (no ElastiCache, no load balancer).
- `deploy.sh` now syncs the systemd service and Nginx config automatically,
  and runs from inside a function so `git pull` can safely update the script
  while it's running.

**Tests:** 12 new consumer tests run the real ASGI stack (origin check →
token middleware → routing → consumer) in memory with Channels'
`WebsocketCommunicator` and an in-memory channel layer (no Redis needed in
tests). Full suite: 111 passing, plus the 7 Selenium UI tests. Also smoke-tested locally against real
Redis + Daphne (`101 Switching Protocols` handshake; foreign origin → 403),
and validated the Nginx config with `nginx -t` in Docker.

---

## 10. Frontend: Friends, Messages, live Chat (branch `sa10-frontend-social`)

**What:** the React pages for connections and chat.
- **Profile page:** Connect button that follows the state: Connect →
  Requested (cancel) → Accept/Decline → Message / Remove.
- **Friends** (`/friends`): Connections and Requests tabs (waiting for you /
  sent by you), with a red badge for new requests.
- **Messages** (`/messages`): chat list with last message, time, and unread
  badges, refreshing every 15 s.
- **Chat** (`/messages/:id`): bubbles, "Load older messages", Enter to send,
  a **Live** indicator, a **"Seen"** receipt, and a read-only notice after
  disconnecting.

**Design decisions / talking points:**
- **All real-time logic lives in one hook** (`useChat`): WebSocket, reconnect
  with backoff (2 s → 30 s), catch-up after reconnecting, read receipts. The
  page component only does layout.
- **Graceful fallback:** if the WebSocket can't connect, the chat quietly
  switches to polling every 3 s and keeps retrying the socket. The badge
  shows "Reconnecting…", so chat never just stops working.
- **No duplicate messages:** messages are merged by id, so the same message
  arriving over both the socket and a catch-up request shows once.
- **Phone-friendly:** checked at 375 px (iPhone width) with no sideways
  scrolling. On phones the logo doubles as the Home link to fit the nav.

**Verified:**
- 3 new Selenium tests (connect → accept → message; send/receive with unread
  badge and read marking; read-only chat after disconnect). They run against
  pytest's plain HTTP test server, so they also prove the polling fallback works.
- Manual two-browser check against the real ASGI server: both windows
  "Live", message delivered in **0.14 s**, "Seen" receipt shown.
- Full suite: 111 unit/API + 10 UI tests passing; lint and production build clean.

---

## 11. Merging a teammate's PR: Discover page (PR #15, `tr2-discover-messages`)
- **What happened:** Trinity built Discover, Chat and Messages pages while I
  was building Chat and Messages too. My PR merged first, so her PR had merge
  conflicts in the two files we both rewrote.
- **How I resolved it:** merged `dev` *into her branch* (not a rebase), so her
  commit stays in the history under her name and no force-push was needed.
  For Chat and Messages I kept the `dev` versions, because they use the real
  `/api/conversations/` endpoints and the live WebSocket; hers called
  `/api/messages/`, which doesn't exist. Her Discover page was kept.
- **Integration fixes on Discover:** Add friend now calls `/api/connections/`
  with the **user id** (it was sending the profile id to a non-existent URL);
  Message now creates/opens the conversation first, then goes to
  `/messages/<conversation id>`; the Friends tab loads real connections from
  the server, so friends survive a refresh.
- **Test:** new Selenium test `test_discover_add_friend_then_message`. I
  checked that it fails on the old page and passes on the fixed one.
- **Talking point:** a merge conflict is Git saying "two people changed the
  same lines; a human has to choose." The lesson: pull `dev` before you start
  a branch, and again before opening a PR.

---

## 12. Profile links + search/filter (branch `sa12-profile-links-search`)
- **Profile links:** students can add up to 5 links (LinkedIn, GitHub,
  Instagram, a portfolio). Stored as a JSON list on Profile, like interests.
- **Why only http(s):** a link is rendered as `<a href>`, and a
  `javascript:` URL there would run code when clicked. The serializer only
  accepts http/https, so that can't happen. Typing `github.com/sam` works:
  the backend adds `https://`.
- **Search/filter:** `GET /api/profiles/` takes `q`, `college`, `interest`,
  `like` and `dislike`. Tag filters use Postgres JSON "contains" (`@>`), so
  `?interest=hiking&interest=coding` means "has both", done in one query.
- **Why on the server, not in the browser:** the old Search tab filtered
  the students already loaded on the page. That stops working once there
  are more students than one page, and it couldn't see likes/dislikes. Now
  the page sends the filters to the API (300 ms after you stop typing) and
  ignores out-of-date responses.
- **Tests:** a parametrized pytest table for every filter, and two Selenium
  tests (add a link and see it on the profile; search by tag and by text).
- **Deploy:** the earlier Discover fix went live first (`deploy.sh dev`).

---

## 13. P8: test cases, automation and CI (branch `sa13-p8-test-cases`)
- **155 automated tests:** 130 pytest unit/API tests and 25 Selenium UI tests.
  Every UI test checks one thing and has an ID (UI-01…UI-25) that matches
  `docs/test-cases.md`.
- **pytest fixtures, in plain words:** a fixture is a setup step a test asks
  for by name. Writing `def test_x(page, alice)` means "before this test,
  give me a fresh browser page and a verified student called alice."
  pytest builds them, hands them in, and cleans up afterwards (empties the
  database, logs out). Fixtures can use other fixtures: `page` needs
  `browser` and `frontend`, so asking for `page` starts Chrome and the
  React server too. Expensive ones (Chrome, the dev server) are
  `scope="session"`, which means they start once for the whole run instead
  of once per test.
- **Selenium waits, in plain words:** the browser is slower than the test
  code. After a click, the page still has to call the API and redraw, so
  checking straight away would fail at random. `wait.until(...)` means
  "keep checking every half second, for up to 10 seconds, until this is
  true," e.g. until the URL contains `/home` or "Requested" appears. It
  moves on the moment it's true, so tests stay fast, and if it never
  happens the test fails with a timeout. We never use `sleep()`.
- **CI (GitHub Actions):** every pull request runs the backend tests, the
  frontend lint + build and the Selenium tests in headless Chrome on a
  fresh Linux machine. Branch protection on `dev`/`main` means a PR can't be
  merged while CI is red. This would have caught the test PR #17 broke.
- **Demo:** `pytest tests_ui --headed -k "ui02 or ui17"` opens Chrome and
  you can watch it reject a gmail signup and send a friend request.

---

## 14. Profile basics: date of birth, gender, city (branch `sa14-profile-basics`)
- **New profile fields:** date of birth (required), gender and city
  (optional). Migration `0004` adds them as nullable columns, so older
  profiles keep working and get asked for a birthday on their next edit.
- **Privacy:** other students see only the **age** worked out from the
  date of birth, never the date. The public serializer doesn't include the
  field at all, and a test checks that the year never appears in the response.
- **18+ only:** the API rejects anyone under 18, future dates and anything
  over 100. The date picker also blocks under-18 dates before sending
  (`max` attribute), but the server check is the real one, because a
  browser check can be bypassed.
- **Search:** `?city=`, `?gender=`, `?min_age=`, `?max_age=`. Ages are
  turned into a date-of-birth range ("at least 22" = born on or before
  this day 22 years ago), so the database does the filtering in one query.
- **Testing trick:** Chrome's date picker types differently per locale
  (mm/dd vs dd/mm), so the Selenium helper `set_date` sets the value
  through JavaScript the way React expects. Same result on any machine or CI.
- **Tests:** 147 unit/API tests and 28 UI tests (new: UI-26 to UI-28).

---

## Git workflow (worth mentioning — version control is 25% of the grade)
- Feature branches per task (`sa1-api-docs`, `sa2-auth`), merged into `dev`
  via pull requests. Teammates use the same flow (`setup-cezar`,
  `add-trinity`).
- Commit after every working checkpoint, with messages that explain *why*,
  not just *what*.
- Pull the latest `dev` into the feature branch before opening a PR, so the
  PR merges cleanly.

---

## Possible demo script (fill in as features land)
1. Open http://18.119.39.20/signup (live) or http://localhost:5173/signup and try a `@gmail.com` address → error
   under the email field.
2. Sign up with a `.edu` address → "Check your inbox" page.
3. Copy the link from the Django terminal and open it → "You're verified".
4. Log in (try a wrong password first to show the error) → profile setup.
5. Fill in bio, interests, a link and the questionnaire → Finish setup → Home shows
   other students; click a card to open their profile.
6. Discover → Search: type a like (e.g. `coffee`) and press Enter; the list
   narrows to students who like it.
7. Run the tests live: `pytest` (API) and `HEADED=1 pytest tests_ui` (watch
   Chrome click through signup and login on its own).
