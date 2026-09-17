# Campus Connect (working title)

Capstone dating app for college students — .edu + ID verification, values-quiz-driven
matching, real-life-meetup features, campus safety tools, anti-burnout capped matching.

## Repo layout

```
campus-connect/
  backend/          Django + DRF + Channels API (this is what's scaffolded so far)
  docker-compose.yml  Postgres + Redis for local dev
  frontend/          React app (not created yet — whoever owns frontend adds this)
```

## One-time setup (run these yourself in your Mac Terminal, not in this chat)

1. Install prerequisites if you don't have them:
   - Python 3.11+ (check with `python3 --version`)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Postgres + Redis)

2. Create and activate a virtual environment:
   ```bash
   cd ~/Documents/Projects/campus-connect/backend
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the env template and fill it in (defaults already match docker-compose):
   ```bash
   cp .env.example .env
   ```

5. Start Postgres + Redis (from the repo root, one level up from backend/):
   ```bash
   cd ..
   docker compose up -d db redis
   ```

6. Run migrations and create your admin login:
   ```bash
   cd backend
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. Run the dev server:
   ```bash
   python manage.py runserver
   ```
   Visit http://127.0.0.1:8000/admin/ — this doubles as the moderation console
   for reviewing .edu/ID verification (see `users/admin.py`).

## Day-to-day

- Activate the venv each new terminal session: `source .venv/bin/activate`
- Start Postgres/Redis before running the server: `docker compose up -d db redis`
- New app: `python manage.py startapp <name>` from inside `backend/`, then add it
  to `INSTALLED_APPS` in `core/settings.py`.
- New model changes: `python manage.py makemigrations && python manage.py migrate`

## What's scaffolded vs. still to build

Done:
- Django project (`core/`) wired for Postgres, Redis/Channels, DRF, CORS
- Custom user model (`users/CustomUser`) with starter .edu/ID verification fields
- Admin panel registered for `CustomUser` (moderation console for verification)

Not yet built (matches the still-open items from planning):
- Matching app (quiz model + scoring engine)
- Chat app (Channels consumers/routing)
- Safety app (walk-me-back, trusted-friend check-in)
- Auth endpoints (.edu domain check, OTP/magic link, DRF serializers/views)
- Frontend (React + Vite + TypeScript + Tailwind)

## Stack reference

See the team's Claude project doc "Tech Stack Recommendation" for the full reasoning
behind these choices (Django vs FastAPI, Cloudinary, Render/Vercel hosting, etc.).
