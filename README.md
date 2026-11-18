# Git Together

[![CI](https://github.com/itssahil2059/campus-connect/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/itssahil2059/campus-connect/actions/workflows/ci.yml)

A social hub for verified college students. Only students with a `.edu` email
can join, and they must verify it. Students build a profile, answer a short
preference questionnaire, find each other through Discover and search,
connect as friends, and chat in real time.

CS 495 Capstone, Texas A&M University–Texarkana, Fall 2026. Team **Git
Together** ([TEAM.md](TEAM.md)).

**Live site:** http://18.119.39.20

## Features

| Area | What it does |
| --- | --- |
| Sign up and verification | `.edu` emails only, one account per email; a verification link must be opened before the first login |
| Login | Token login and logout; private pages redirect to login |
| Profile | Bio, interests, likes, dislikes, up to 5 links, age, gender, city. Date of birth is required (18+) but kept private: others only see the age |
| Questionnaire | Multiple-choice preference questions, saved to the account and editable later |
| Home feed | Other verified students (never yourself) |
| Discover | Browse everyone, see your friends, and search |
| Search and filter | Keyword search plus filters for college, city, gender, age range, interests, likes and dislikes |
| Friends | Send, accept, decline, cancel and remove friend requests; your connections are private |
| Messages | Private one-to-one chats between friends, delivered live over WebSockets, with unread badges and read receipts |

## Tech stack

| Part | Tech |
| --- | --- |
| Backend API | Python, Django 5, Django REST Framework (token auth) |
| Realtime chat | Django Channels + Redis |
| Database | PostgreSQL 16 |
| Frontend | React, Vite, TypeScript, Tailwind CSS |
| Hosting | AWS EC2 (Nginx + Daphne) and AWS RDS (PostgreSQL) |
| Tests | pytest + pytest-django (unit/API), Selenium (UI automation) |
| CI | GitHub Actions on every pull request |

## Tests

| Suite | Tests | Command (from `backend/`) |
| --- | --- | --- |
| Unit + API (pytest) | 147 | `pytest` |
| UI automation (Selenium, Chrome) | 28 | `pytest tests_ui` |
| **Total** | **175** | |

Every test case, with its steps, expected result and the project task it
covers, is listed in [docs/test-cases.md](docs/test-cases.md). Add
`--headed` to watch Chrome run the UI tests.

## Running it locally

You need Python 3.11+, Node.js 20.19+, Docker Desktop and Google Chrome (for
the UI tests).

```bash
docker compose up -d db redis                  # Postgres + Redis

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver                     # API on http://127.0.0.1:8000

cd ../frontend                                 # in a second terminal
npm install
npm run dev                                    # app on http://localhost:5173
```

In local development the verification email is printed in the `runserver`
terminal instead of being sent. Full setup, troubleshooting and the team's git
workflow are in [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

## Project layout

```
backend/
  core/          Django settings and URLs
  users/         Accounts: signup, email verification, login/logout
  profiles/      Profiles, questionnaire, search
  connections/   Friend requests and connections
  chat/          Conversations, messages, WebSocket consumer
  tests_ui/      Selenium UI tests
frontend/        React app (pages in src/pages, shared UI in src/components)
deploy/          EC2 server config and deploy script
docs/            API reference, deployment guide, test cases
```

## Documentation

- [API reference](docs/api.md)
- [Test cases](docs/test-cases.md)
- [Deployment guide (AWS)](docs/deploy.md)
- [Developer guide](docs/CONTRIBUTING.md)
