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
5. Fill in bio, interests and the questionnaire → Finish setup → Home shows
   other students; click a card to open their profile.
6. Run the tests live: `pytest` (API) and `HEADED=1 pytest tests_ui` (watch
   Chrome click through signup and login on its own).
