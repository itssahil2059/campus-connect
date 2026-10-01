# Git-Together API (planned)

Base URL (local): http://127.0.0.1:8000
All responses are JSON. The frontend's `api/client.ts` converts snake_case to camelCase.

## Auth (Weeks 2–3)
| Method | Path | Purpose |
| --- | --- | --- |
| POST | /api/auth/signup/ | Create account (.edu email only), sends verification email |
| GET | /api/auth/verify/<uid>/<token>/ | Activate account from email link |
| POST | /api/auth/login/ | Returns login token |
| POST | /api/auth/logout/ | Ends session |
| GET | /api/auth/me/ | Current logged-in user |

## Profiles & questionnaire (Weeks 4–5)
| Method | Path | Purpose |
| --- | --- | --- |
| GET / PUT | /api/profiles/me/ | My profile |
| GET | /api/profiles/<id>/ | Another student's profile |
| POST | /api/profiles/me/photo/ | Upload profile photo |
| GET | /api/questions/ | Questionnaire questions |
| GET / POST | /api/answers/ | My questionnaire answers |

## Discovery, search, connections (Weeks 6–7)
| Method | Path | Purpose |
| --- | --- | --- |
| GET | /api/discover/ | Suggested students, best match first |
| GET | /api/search/?q=&college=&interest= | Search and filter |
| GET / POST | /api/connections/ | My connections / send a request |
| POST | /api/connections/<id>/accept/ | Accept a request |
| POST | /api/connections/<id>/decline/ | Decline a request |
| DELETE | /api/connections/<id>/ | Remove a connection |

## Messaging (Week 8)
| Method | Path | Purpose |
| --- | --- | --- |
| GET | /api/conversations/ | My chats |
| GET | /api/conversations/<id>/messages/ | Chat history |
| WebSocket | /ws/chat/<id>/ | Live messages |
