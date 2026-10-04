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
### Step (e): Automated tests — *not started*
### Step (f): Push branch + pull request into `dev` — *not started*

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
1. Show signup rejecting a `@gmail.com` address.
2. Sign up with a `.edu` address → show the user is inactive in the admin.
3. Show the verification link printed in the terminal,
   click it, then log in and call `/api/auth/me/` with the token.
4. *(after step e)* Run the test suite live: `pytest`.
