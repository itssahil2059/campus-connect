# Campus Connect — Claude Code project rules

## What this is
Capstone dating app for college students. Differentiators: strict .edu + ID
verification, values/lifestyle quiz drives matching (not just photo-swiping),
features that push matches toward real meetups fast, campus safety tools
(walk-me-back, trusted-friend check-in), anti-burnout capped daily matches.

Sahil owns the backend (Software Developer role). He's comfortable in Python,
learning Django/DRF/React as he goes, and building this partly as a portfolio
piece for his job search — so explain non-obvious decisions briefly rather than
just producing code silently. Don't over-explain trivial stuff.

## Stack
- Backend: Django + Django REST Framework, Python 3.11+
- DB: PostgreSQL (via docker-compose, local dev)
- Realtime: Django Channels + Redis (chat)
- Frontend: React + Vite + TypeScript + Tailwind (not built yet)
- Media: Cloudinary (planned, not wired up yet)
- Hosting target: Render (backend/db/redis) + Vercel (frontend) — not deployed yet

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
  (users, matching, chat, safety — not one giant app).
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
- Local git repo only as of today — not pushed to GitHub yet. Once a remote
  is added, push after every checkpoint (see working agreement above), not
  just at feature-complete milestones.

## Not yet built
- Auth endpoints (.edu domain check, OTP/magic link, serializers/views)
- Matching app (quiz model + weighted scoring engine)
- Chat app (Channels consumers/routing)
- Safety app (walk-me-back, trusted-friend check-in)
- Frontend (React + Vite + TS + Tailwind)
