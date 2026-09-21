# Campus Connect — Claude Code project rules

## What this is
Capstone dating app for college students ("Campus Connect" is just a placeholder
name — not officially decided by the team yet). Core idea: an online social/dating
hub for college students, differentiated by strict .edu + verification, a
values/lifestyle quiz that drives matching (not just photo-swiping), features that
push matches toward real meetups fast, campus safety tools (walk-me-back,
trusted-friend check-in), and anti-burnout capped daily matches.

Sahil owns the backend (Software Developer role). He's comfortable in Python,
learning Django/DRF/React as he goes, and building this partly as a portfolio piece
for his job search — so explain non-obvious decisions briefly rather than just
producing code silently. Don't over-explain trivial stuff. Sahil generally wants to
attempt things himself first and have mistakes pointed out, rather than getting
full implementations handed to him by default — ask before writing a large chunk of
a new feature outright; smaller mechanical fixes are fine to just make.

## Team
- Software Developer: Sahil Bhusal (this repo's primary user)
- Tech Support: Cezar Herrera
- Scribe: Trinity Rodriguez
- Team Leader / Architect / QA: unassigned as of Sep 2026

## Stack
- Backend: Django + Django REST Framework, Python 3.11+
- DB: PostgreSQL (via docker-compose, local dev)
- Realtime: Django Channels + Redis (chat)
- Frontend: React + Vite + TypeScript + Tailwind (not built yet)
- Media: Cloudinary (planned, not wired up yet)
- Hosting target: Render (backend/db/redis) + Vercel (frontend) — not deployed yet
- Auth: DRF TokenAuthentication (already in settings.py) — not JWT.
- Email verification: reuse `django.contrib.auth.tokens.default_token_generator`
  (same mechanism Django uses for password reset) rather than a custom token
  scheme. Use the console email backend for local dev — no real email service
  wired up yet.

## Repo layout
```
campus-connect/
  backend/
    core/        Django project (settings, urls, asgi/wsgi)
    users/       Custom user model + auth/verification (in progress)
  docker-compose.yml   Postgres + Redis for local dev
  frontend/            Not created yet
```

## Running it locally
```bash
cd backend
source .venv/bin/activate          # create with `python3 -m venv .venv` if missing
pip install -r requirements.txt
cd .. && docker compose up -d db redis
cd backend
python manage.py migrate
python manage.py runserver
```

## Conventions
- Follow standard Django app structure: one app per bounded feature area
  (users, matching, discovery, chat, safety — not one giant app).
- DRF: serializers + viewsets, not function-based views, unless there's a
  good reason.
- Run `python manage.py makemigrations` + commit the migration file in the
  same commit as the model change that produced it.
- New Python deps go in `requirements.txt` with a version floor (`>=`), not
  pinned exact versions, unless there's a compatibility reason to pin.

## Working agreement
- Commit after every working checkpoint, not just at the end of a feature.
- For anything architectural (new app, schema change, auth/verification
  flow, matching engine design) — explain the approach and tradeoffs before
  writing the code, don't just generate it.
- For small mechanical changes (a field, a bugfix, boilerplate matching an
  existing pattern) — just make the change, brief note is enough.
- Don't add major new dependencies (a new framework, a paid API integration)
  without flagging it first — some of these are cost/scope decisions for the
  whole team, not just this repo.
- Don't change `AUTH_USER_MODEL` or squash/rewrite existing migrations
  without flagging it — both are painful to undo once other code depends on
  them.

## Git / GitHub
- Local git repo, not yet pushed to GitHub as of Sep 21 2026 — push planned soon.
  Once a remote is added, push after every checkpoint, not just at
  feature-complete milestones.

## Build order (dependency-first — build in this order, don't jump ahead)
1. **User auth + .edu verification** — signup, login, school-email domain check,
   email verification via `default_token_generator`. **← current step.**
2. Profile creation + preference quiz (incl. image upload via Cloudinary, and an
   "insert links" field).
3. Suggested Interest / discovery feed — looser, randomized browse surface
   ("like YouTube subscriptions" per the team's own description).
4. Search/Filter — precise narrowing (name, college, interests, likes/dislikes).
5. Connections ("interest"/"friend") — private to the user, others can't see who
   you've added.
6. Messaging/chat — multiple private chats. **Open question below** on whether
   this requires an existing connection first.

## Open product questions (need a team decision, not blockers to keep coding)
- Does messaging require an existing connection ("friend"/interest) first, or can
  any user message any other user directly from their profile? Team's notes list
  both as separate abilities from a profile, which reads as open messaging —
  flagged as a safety concern (harassment/spam risk), recommendation is to require
  a connection first for MVP. Confirm with team before building the chat app (step 6).
- Real project name not yet decided (still just "campus-connect" placeholder).
- Team Leader / Architect / QA roles still unassigned.

## Not yet built
- Auth endpoints (.edu domain check, verification, login) — in progress now
- Matching app (quiz model + weighted scoring engine)
- Discovery/search apps
- Chat app (Channels consumers/routing)
- Safety app (walk-me-back, trusted-friend check-in)
- Frontend (React + Vite + TS + Tailwind)
