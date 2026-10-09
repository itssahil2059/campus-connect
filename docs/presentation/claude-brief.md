# Presentation Brief — Git Together prototype (for Claude chat)

> **To Claude:** this file is the complete, accurate record of the project so far.
> Use only the facts here — don't invent features, numbers, or results. If
> something a slide needs isn't in here, mark it as **[TODO: confirm]**
> instead of guessing. Screenshots referenced below are attached separately
> (`screenshots/*.png`).

---

## 1. The project in one paragraph

**Git Together** (working title "Campus Connect"; the final product name isn't
decided yet — "Git Together" is the team name) is a social hub for verified
college students. Only students with a `.edu` email can join, and they must
verify it. Each student builds a profile (bio, interests, likes, dislikes)
and answers a short preference questionnaire, then browses other verified
students. The long-term vision adds values-based matching, features that move
connections toward real-life meetups, campus safety tools (walk-me-back,
trusted-friend check-in), and capped daily matches to prevent burnout.

**Course:** CS 495 Capstone, Texas A&M University–Texarkana, Fall 2026,
instructor Dr. Bo Guo.

**Team** (from the repo's TEAM.md — confirm before presenting):
| Name | Role |
| --- | --- |
| Sahil Bhusal | Software Developer (built the prototype: backend, frontend, tests) |
| Cezar Herrera | Tech Support |
| Trinity Rodriguez | Team Lead / Scribe (building the landing page on a separate branch) |
| Christian Martinez | Team member — role TBD **[TODO: confirm]** |

---

## 2. The problem and our answer

**Problem:** general social and dating apps aren't built for campus life. Anyone
can sign up (fake or non-student accounts), matching is mostly photo-swiping,
and connections rarely turn into real meetups.

**Our answer / differentiators:**
1. **Verified students only** — `.edu` email required and verified before login.
2. **Values/preference questionnaire** — matching driven by what you're
   like, not just photos (the questionnaire exists now; the matching engine is
   next).
3. **Real-life focus** — features that push connections toward meeting up
   (planned).
4. **Safety tools** — walk-me-back, trusted-friend check-in (planned).
5. **Anti-burnout** — capped daily matches (planned).

---

## 3. What the prototype does (demo scope)

One complete flow a user can click through:

**Sign up (.edu only) → verify email → log in → set up profile + questionnaire
→ Home feed of other students → view a student's profile**

| Screen | What it shows | Screenshot |
| --- | --- | --- |
| Sign up | Username, school email, college, password; errors appear under the field | `01-signup.png`, `02-signup-edu-error.png` |
| Check your inbox | Confirms the verification email was sent | `03-check-email.png` |
| Verified | Opened from the emailed link; account activated | `04-verified.png` |
| Log in | School email + password; clear error messages | `05-login-error.png` |
| Profile setup | Bio, interest/like/dislike tags, 5-question questionnaire | `06-profile-setup.png` |
| Home | Cards of other verified students | `07-home-feed.png` |
| Profile view | One student's full profile | `08-profile-view.png` |
| Mobile | Same pages on a phone-size screen | `09-home-mobile.png`, `10-signup-mobile.png` |

**Questionnaire questions (stored in the database, editable from the admin):**
1. What are you mainly looking for? (New friends / Study partners / Dating / Not sure yet)
2. Your ideal weekend? (Out with a big group / Small hangout / Outdoors / Staying in)
3. How do you like to study? (Quiet library / Coffee shop / Group study / Last-minute cram)
4. What's your sleep schedule? (Early bird / Night owl / Depends on the day)
5. How often do you want to meet up in person? (A few times a week / Weekends / Once in a while)

---

## 4. Architecture

```
 Browser (React app, port 5173)
        │  JSON over HTTP, header: "Authorization: Token <key>"
        ▼
 Django + Django REST Framework API (port 8000)
   ├─ users app     → signup, email verification, login/logout, /me
   └─ profiles app  → profiles, questionnaire questions & answers
        │
        ▼
 PostgreSQL database  (Redis is also running, reserved for real-time chat later)
```

- Local development uses **Docker** for Postgres and Redis, so every
  teammate gets an identical database with one command.
- **Planned hosting: AWS** (EC2 or Elastic Beanstalk for the API, RDS for
  Postgres, S3 + CloudFront for the frontend, SES for real emails). **Not
  deployed yet.**

### Tech stack and why

| Layer | Choice | Why |
| --- | --- | --- |
| Backend | Python, Django 5, Django REST Framework | Built-in admin, auth, and security; fast to build a reliable API |
| Auth | DRF token authentication | Simple for a React app on a different port; logout truly revokes the token |
| Database | PostgreSQL 16 | Production-grade; same database locally and in production (AWS RDS) |
| Frontend | React + Vite + TypeScript + Tailwind CSS | Fast dev server, type safety, quick consistent styling |
| Tests | pytest + pytest-django; Selenium (Python) | API tests run in seconds; Selenium meets the instructor's UI-automation requirement |
| Dev environment | Docker Compose | Same Postgres/Redis setup for everyone |
| Version control | Git + GitHub, branch per task, pull requests into `dev` | Clean history; version control is graded |

### API endpoints built

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/auth/signup/` | Create account (.edu only), send verification email |
| GET | `/api/auth/verify/<uid>/<token>/` | Activate account from the email link |
| POST | `/api/auth/login/` | Email + password → auth token |
| POST | `/api/auth/logout/` | Revoke the token |
| GET | `/api/auth/me/` | Current user |
| GET / PUT | `/api/profiles/me/` | My profile (404 until set up → frontend shows setup) |
| GET | `/api/profiles/` | Home feed: other verified, active students |
| GET | `/api/profiles/<id>/` | One student's profile (never includes email) |
| GET | `/api/questions/` | Questionnaire |
| GET / POST | `/api/answers/` | My answers (saved all-or-nothing) |

---

## 5. Key design and security decisions (good talking points)

1. **Accounts start locked.** New users are created inactive; Django's
   login refuses inactive users, so nobody can log in before verifying.
2. **Verification without storing secrets.** The email link contains the
   user's id (base64) and a token from Django's built-in
   `default_token_generator` — the same mechanism Django uses for password
   resets. It's signed with the server's secret key, nothing is stored in the
   database, it expires after 3 days, and it stops working after the first
   login.
3. **No account enumeration.** "Wrong password" and "no such email" return
   the same message, so attackers can't discover who has an account.
4. **Old links can't undo a ban.** Verification only activates users who
   were never verified, so if an admin deactivates someone, an old link
   can't reactivate them.
5. **Emails are case-insensitive.** `Sahil@TAMUT.EDU` and `sahil@tamut.edu`
   are treated as the same account.
6. **Strong passwords.** Django's validators reject short, common, all-numeric,
   or too-similar-to-your-email passwords.
7. **Privacy by design.** Other students never see your email; there are two
   different serializers for "me" and "everyone else".
8. **The feed only shows verified, active students.**
9. **Questions live in the database**, so new questions can be added from
   the admin panel without changing code.
10. **Email goes to the terminal in development** (Django console email
    backend); switching to real email (AWS SES) is a configuration change, not a
    code change.

---

## 6. Testing (instructor requires UI automation)

| Suite | Tool | Tests | Runtime |
| --- | --- | --- | --- |
| API / unit | pytest + pytest-django | **49** | ~5 s |
| UI automation | Selenium + Chrome | **7** | ~10 s |
| **Total** | | **56, all passing** | |

**API tests cover:** signup rules (.edu, duplicates in any case, password
rules, required fields, password stored hashed, verification email sent);
verification (full signup → email link → verify → login flow, tampered
tokens, another user's token, garbage links, already verified, banned users,
link invalid after login); login/logout (token returned, case-insensitive
email, generic error, `/me` needs login, logout revokes token); profiles
(create/update, tag clean-up, tag limit, feed excludes self/unverified/
banned/profile-less users, no email in public profiles); questionnaire
(questions seeded, answers saved/replaced, invalid choice rolls back the
whole batch, you only see your own answers).

**UI tests (real Chrome clicking real pages) cover:** non-.edu email error;
duplicate email error; **full signup → open the emailed link → verified →
login → profile setup**; wrong password error; unverified user blocked; login
→ Home → logout; logged-out visitor redirected to login.

How the UI tests work: each run starts its own Django server on a throwaway
test database and its own React server, then drives Chrome. Selenium even
reads the verification link from the captured test email, so the "check your
inbox" step is automated. `HEADED=1 pytest tests_ui` shows the browser live.

### Bugs found by testing (and fixed)

1. **Duplicate-email message was generic.** DRF's automatic uniqueness
   check ran before ours and was case-sensitive → replaced with one
   case-insensitive check and a clear message.
2. **Password errors appeared twice.** The password-similarity validator was
   listed twice in settings → removed the duplicate and added a regression test.
3. **"Not logged in" returned 403 instead of 401.** DRF uses the first
   authentication class for that response → reordered so the frontend gets a
   correct 401.
4. **Wrong password showed no error on the login page.** Found by the
   browser walkthrough — the general error was being treated as a field
   error → fixed in the shared API helper, so every form benefits.

Lesson: test the error paths, not just the happy path, and pair every bug fix
with a test.

---

## 7. Version control

- GitHub repo with a **branch per task** (`sa2-auth` → `sa3-profiles` →
  `sa4-frontend-flow`), merged into `dev` through pull requests; teammates
  use the same flow (`setup-cezar`, `add-trinity`, `tr1-home-page`).
- Small commits after every working step, with messages that explain why.
- **Sahil's commits for this prototype: 13** (Sep 30 – Oct 4, 2026), on top of
  the initial scaffold (Sep 17) — custom user model, Docker setup, frontend
  skeleton, API plan.

### Timeline
| Date (2026) | Milestone |
| --- | --- |
| Sep 17 | Django backend scaffolded: custom user model, Postgres + Redis in Docker |
| Sep 23 | First signup endpoint |
| Sep 30 – Oct 1 | Frontend skeleton (React/Vite/Tailwind, routes) + planned API list |
| Oct 2 | Signup locked until verified; verification email |
| Oct 4 | Login/logout/me, profiles + questionnaire, full frontend flow, 56 tests, README |

---

## 8. Live demo script (~3 minutes)

1. Open `http://localhost:5173/signup`. Try a `@gmail.com` address → the error
   appears under the email field.
2. Sign up with a `.edu` address → "Check your inbox".
3. Show the terminal where the verification email printed; open the link →
   "You're verified".
4. Log in — first with a wrong password (show the error), then correctly →
   lands on profile setup.
5. Fill in bio, interests, and the questionnaire → Finish setup → Home shows
   other students; click a card to open a profile.
6. Run `HEADED=1 pytest tests_ui` → Chrome clicks through signup and login
   by itself; then `pytest` → 49 API tests pass in seconds.

Backup plan if something breaks live: use the screenshots.

---

## 9. Honest limitations (don't claim these are done)

- Not deployed to AWS yet — runs locally.
- No real emails yet (printed to the terminal in development).
- No matching engine yet — answers are saved but not used for ranking.
- No chat, search, connections, safety features, or photo upload yet.
- The design is a placeholder; the team's UX designs will replace it.
- The landing page (`/`) is a teammate's separate branch, not merged yet.

## 10. What's next (roadmap)

1. Merge the three branches into `dev` via pull requests.
2. Deploy a basic version to AWS (EC2/RDS/S3) early, so it isn't a last-week scramble.
3. Profile photo upload (AWS S3) and a links field.
4. Discovery feed → search/filter → connections → messaging (in that order).
5. Matching engine using questionnaire answers; safety tools; capped daily matches.

**Open team decisions:**
- Should messaging require an existing connection first? (Recommended yes,
  for safety and anti-spam.)
- Framing: the proposal says "social hub", while the plan includes dating
  features — the paper or the scope should match.
- Final product name; Team Leader / Architect / QA roles.

---

## 11. Suggested slide outline (10–12 slides)

1. **Title** — Git Together: a verified social hub for college students. Team names, course.
2. **The problem** — why general apps fail students (section 2).
3. **Our solution & differentiators** — the 5 points.
4. **Prototype demo flow** — the 6-step flow as a visual, with small screenshots.
5. **Architecture** — the diagram from section 4.
6. **Tech stack & why** — the table, condensed.
7. **Security & privacy decisions** — pick 4–5 from section 5.
8. **Screens** — 3–4 best screenshots (signup error, profile setup, home feed, mobile).
9. **Testing** — 56 tests, the UI-automation requirement met, the bugs testing caught.
10. **Version control & process** — branch-per-task, PRs, timeline.
11. **Limitations & next steps** — sections 9–10.
12. **Live demo / Q&A**.

Style: clean and minimal to match the app — warm cream background
(#faf7f2), dark ink text (#1f1b16), one coral accent (#e0564f), serif
headings (Fraunces) and sans-serif body (Inter).
