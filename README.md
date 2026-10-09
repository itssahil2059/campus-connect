# Git Together (working title: Campus Connect)

A social hub for verified college students. Sign up with a `.edu` email, verify
it, build a profile and answer a short preference questionnaire, then browse
other verified students.

CS 495 Capstone, Texas A&M University–Texarkana, Fall 2026 — team **Git
Together** (see [TEAM.md](TEAM.md)).

## What works today

Signup (`.edu` only) → email verification link → login → profile + preference
questionnaire → Home feed of other students → single profile view.

| Part | Tech |
| --- | --- |
| Backend API | Django 5 + Django REST Framework, token auth |
| Database | PostgreSQL 16 (Docker for local dev) |
| Realtime (later, for chat) | Redis 7 (Docker) + Django Channels |
| Frontend | React + Vite + TypeScript + Tailwind |
| Tests | pytest + pytest-django (API), Selenium (UI automation) |

API endpoints: [docs/api.md](docs/api.md).

## Repo layout

```
campus-connect/
  backend/
    core/        Django project: settings, URLs
    users/       Accounts: signup, email verification, login/logout, /me
    profiles/    Profiles + questionnaire (Question/Answer), seed_demo command
    tests_ui/    Selenium browser tests
  frontend/      React app (pages in src/pages, shared UI in src/components)
  docs/          API list, presentation notes
  docker-compose.yml   Postgres + Redis for local dev
```

---

## First-time setup

### 1. Install prerequisites

- **Python 3.11+** — check with `python3 --version`
- **Node.js 22+** (or 20.19+) — check with `node --version`
- **Docker Desktop** — https://www.docker.com/products/docker-desktop/
- **Google Chrome** — only needed for the UI tests

### 2. Get the code

```bash
git clone https://github.com/itssahil2059/campus-connect.git
cd campus-connect
```

### 3. Start the database (Postgres + Redis)

Open **Docker Desktop** first and wait until it says "Engine running", then:

```bash
docker compose up -d db redis
docker compose ps        # both should say "Up"
```

### 4. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # defaults already match docker-compose
python manage.py migrate           # creates tables + the starter questionnaire
python manage.py seed_demo         # optional: 6 sample students for the Home feed
python manage.py createsuperuser   # optional: login for the admin site
```

### 5. Frontend setup

In a **second terminal**:

```bash
cd frontend
npm install
```

---

## Running the app

You need **two terminals** (plus Docker running).

**Terminal 1 — backend** (http://127.0.0.1:8000)

```bash
cd backend
source .venv/bin/activate
python manage.py runserver
```

**Terminal 2 — frontend** (http://localhost:5173)

```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173/signup**.

### Trying the full flow

1. Sign up with any address ending in `.edu` (it doesn't have to be real).
2. **No real email is sent in local dev.** The verification email, including
   the link, is printed in **Terminal 1**. Copy the link
   (`http://localhost:5173/verify/...`) into your browser.
3. Log in → you'll land on profile setup the first time → fill it in → Home.

Shortcut: after `seed_demo`, you can log in as any sample student, e.g.
`maya@tamut.edu` / `demo-Pass-2026`.

Admin site (users, profiles, questions, tokens): http://127.0.0.1:8000/admin/

---

## Running the tests

From `backend/` with the venv active:

```bash
pytest                    # API tests (fast, ~5s)
pytest tests_ui           # Selenium browser tests (~10s)
HEADED=1 pytest tests_ui  # same, but watch Chrome click through
```

- Tests use a separate throwaway database, so your local data is never touched.
- The UI tests start their own backend and frontend servers (frontend on
  port **5174**), so you don't need anything running except Docker. Run
  `npm install` in `frontend/` first.

---

## Day-to-day

- New terminal? `cd backend && source .venv/bin/activate`
- Docker Desktop must be running, and `docker compose up -d db redis` once per reboot.
- Pulled new code? Run `pip install -r requirements.txt`, `python manage.py migrate`,
  and `npm install` in `frontend/` in case dependencies or the schema changed.
- Changed a model? `python manage.py makemigrations`, then commit the migration
  file **in the same commit** as the model change.

### Git workflow

- Never commit directly to `main` or `dev`. One branch per task:
  ```bash
  git switch dev && git pull
  git switch -c <initials><number>-<short-name>   # e.g. sa3-profiles
  ```
- Commit after every working step, with a message that says what and why.
- `git push -u origin <branch>` the first time, then just `git push`.
- Open a pull request into **`dev`** on GitHub when the task is done.
- Never commit `backend/.env` (it holds secrets; it's already git-ignored).

---

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `failed to connect to the docker API` | Docker Desktop isn't running — open it and wait. |
| `connection refused` on port 5432 when running Django | `docker compose up -d db redis` from the repo root. |
| Frontend says "Can't reach the server" | Terminal 1 (`runserver`) isn't running. |
| Login says "Please verify your email" | Open the verification link printed in Terminal 1. |
| Verification link says invalid/expired | Links expire after 3 days and stop working after your first login — sign up again with a new email. |
| `port 5174 is already in use` (UI tests) | Another Vite server is on 5174 — stop it and rerun. |
