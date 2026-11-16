# Git Together — Test Cases (P8)

Testing tools (approved by the instructor in place of JUnit):

- **pytest + pytest-django**: unit and API tests, one `tests/` folder per Django app.
- **Selenium (Python bindings)**: UI automation. A real Chrome browser clicks
  through the real React pages, which talk to a real (test) Django server.

> **Requirements:** the last column traces each test to the task it verifies
> in our Phase 3 project plan (Tasks T1–T10). T1 (repo, roles, theme) is
> project setup, so it has no UI test.

## How to run

```bash
cd backend
source .venv/bin/activate
docker compose -f ../docker-compose.yml up -d db   # Postgres for the test database

pytest                       # unit + API tests (fast, ~25 s)
pytest tests_ui              # UI tests, headless Chrome (~35 s)
pytest tests_ui --headed     # UI tests in a visible Chrome window (for demos)
pytest tests_ui -k ui05      # one UI test by ID
```

The UI tests start everything they need on their own: a throwaway Django server
on an empty test database, the React dev server pointed at it (port 5174),
and Chrome. CI runs both suites on every pull request (`.github/workflows/ci.yml`).

## UI test cases (Selenium) — 28 tests

Every test starts logged out with an empty database and creates only the data
it needs. "Steps" are what the browser does; "Expected" is the main check.
Files are in `backend/tests_ui/`.

### Landing page, signup and verification (`test_auth_flow.py`)

| ID | Test name | What it tests | Steps | Expected result | Requirement (Phase 3 task) |
| --- | --- | --- | --- | --- | --- |
| UI-01 | `test_ui01_landing_page_sign_up_button_opens_signup` | Landing page loads and leads to signup | Open `/`; click **Sign up** in the header | Headline "Meet students who get you." shows; URL becomes `/signup` | T2 Registration/Authentication |
| UI-02 | `test_ui02_signup_rejects_non_edu_email` | Only school emails can sign up | Open `/signup`; fill the form with `sahil@gmail.com`; submit | Error "Please use your .edu school email." under the email field | T2 Registration/Authentication |
| UI-03 | `test_ui03_signup_rejects_duplicate_email` | One account per email, case-insensitive | Account `sahil@tamut.edu` exists; sign up with `SAHIL@tamut.edu` | Error "An account with this email already exists." | T2 Registration/Authentication |
| UI-04 | `test_ui04_signup_with_edu_email_asks_to_check_inbox` | Valid .edu signup | Sign up with `sahil@tamut.edu` | Goes to `/check-email` showing the address; a verification email is sent to it | T2 Registration/Authentication |
| UI-05 | `test_ui05_verification_link_activates_account` | Email verification link | Unverified account exists; open its `/verify/<uid>/<token>` link | Page says "verified"; account becomes active and .edu-verified | T2 Registration/Authentication |
| UI-06 | `test_ui06_login_with_wrong_password_shows_error` | Wrong password is refused | Log in with the right email and a wrong password | Alert "Invalid email or password."; still on `/login` | T2 Registration/Authentication |
| UI-07 | `test_ui07_unverified_user_cannot_log_in` | Verification is required before login | Unverified account; log in with the right password | Alert "Please verify your email before logging in." | T2 Registration/Authentication |
| UI-08 | `test_ui08_first_login_goes_to_profile_setup` | New users are sent to build a profile | Verified account with no profile; log in | URL becomes `/profile/setup` | T2 Registration/Authentication / T3 Profile Creation |
| UI-09 | `test_ui09_successful_login_lands_on_home` | Successful login | Verified account with a profile; log in | Home shows "Hey, alice"; a login token is stored | T2 Registration/Authentication |
| UI-10 | `test_ui10_logged_out_visitor_is_redirected_to_login` | Private pages need login | Logged out, open `/home` | Redirected to `/login` | T2 Registration/Authentication |
| UI-11 | `test_ui11_logout_clears_session` | Logout | Log in; click **Log out** | Redirected to `/login`; the token is removed from the browser | T2 Registration/Authentication |

### Profile, questionnaire, feed and search (`test_profile_flow.py`)

| ID | Test name | What it tests | Steps | Expected result | Requirement (Phase 3 task) |
| --- | --- | --- | --- | --- | --- |
| UI-12 | `test_ui12_questionnaire_answers_are_saved` | Preference questionnaire | New user on `/profile/setup`; pick "Night owl" for "Are you a morning person?"; click **Finish setup** | Goes to `/home`; the answer "Night owl" is saved | T4 Preference Questionnaire |
| UI-13 | `test_ui13_feed_lists_other_students_not_yourself` | Home feed | Alice and Bob have profiles; Alice opens `/home` | Exactly one card: Bob (never yourself) | T6 Discovery Page |
| UI-14 | `test_ui14_profile_link_shows_on_profile_page` | Profile "insert links" field | Alice adds `github.com/alice` on `/profile/edit` and saves; Bob opens Alice's profile | A link to `https://github.com/alice` is shown | T3 Profile Creation / T5 Profile Page |
| UI-15 | `test_ui15_search_filters_by_like_tag` | Search by likes | Discover → Search shows Bob and Carol; type `coffee` in **Likes**, press Enter | Only Bob (who likes coffee) is listed | T7 Search and Filtering |
| UI-16 | `test_ui16_search_matches_bio_text` | Search by text | Discover → Search; type `night owl` in the search box | Only Carol (bio "Night owl") is listed | T7 Search and Filtering |
| UI-26 | `test_ui26_profile_shows_age_gender_city_not_birthday` | Age, gender and city on a profile; birthday stays private | Alice sets date of birth, gender "Woman" and city "Texarkana" on `/profile/edit`; Bob opens her profile | Bob sees "<age> · Woman · Texarkana"; the birth date appears nowhere on the page | T3 Profile Creation / T5 Profile Page |
| UI-27 | `test_ui27_under_18_birthday_is_blocked` | Adults only (18+) | New user on `/profile/setup` enters a birthday 17 years and 364 days ago; clicks **Finish setup** | The date field is invalid and no profile is saved | T2 Registration/Authentication / T3 Profile Creation |
| UI-28 | `test_ui28_search_filters_by_city` | Search by city | Discover → Search (Bob in Dallas, Carol in Texarkana); type `texarkana` in **City** | Only Carol is listed | T7 Search and Filtering |

### Friends, chat and Discover (`test_social_flow.py`)

| ID | Test name | What it tests | Steps | Expected result | Requirement (Phase 3 task) |
| --- | --- | --- | --- | --- | --- |
| UI-17 | `test_ui17_connect_sends_friend_request` | Sending a friend request | Alice opens Bob's profile; clicks **Connect** | Button area shows "Requested"; a pending request is saved | T8 Friending |
| UI-18 | `test_ui18_accepting_request_connects_both_students` | Accepting a friend request | Alice has requested Bob; Bob opens `/friends`; clicks **Accept** | Request leaves the list; the connection is accepted | T8 Friending |
| UI-19 | `test_ui19_message_button_opens_chat_with_friend` | Starting a chat with a friend | Alice and Bob are friends; Alice opens Friends → Connections; clicks **Message** | Opens `/messages/<id>` for their conversation | T8 Friending / T9 Private Messages |
| UI-20 | `test_ui20_sending_a_message_shows_it_in_chat` | Sending a message | Alice opens the chat with Bob; types "hi bob", presses Enter | "hi bob" appears in the chat and is saved | T9 Private Messages |
| UI-21 | `test_ui21_unread_message_shows_badge_in_chat_list` | Unread messages | Bob sent "hey alice!"; Alice opens `/messages` | The chat row shows the message and an unread badge "1" | T10 Message Hub |
| UI-22 | `test_ui22_new_message_appears_without_reload` | Receiving messages live | Alice has the chat open; Bob sends "how's it going?" | The message appears without reloading the page | T9 Private Messages |
| UI-23 | `test_ui23_chat_after_disconnect_is_read_only` | Chat needs a connection | Alice and Bob have a chat but aren't connected; Alice opens it | "no longer connected" shown; no message box | T9 Private Messages |
| UI-24 | `test_ui24_discover_connect_sends_friend_request` | Connecting from Discover | Alice opens Discover → Everyone; clicks **Connect** on Bob's card | Card shows "Requested"; request from Alice to Bob saved | T6 Discovery Page / T8 Friending |
| UI-25 | `test_ui25_discover_remove_takes_friend_off_friends_tab` | Removing a friend | Alice and Bob are friends; Discover → Friends; click **Remove**, confirm | Bob's card disappears; the connection is deleted | T6 Discovery Page / T8 Friending |

### Planned but not built yet (so not tested yet)

| Phase 3 task | Requirement | Status |
| --- | --- | --- |
| T3 Profile Creation | Upload a profile image, or pick a default one | Not built (needs S3) |
| T4 Preference Questionnaire | After the questionnaire, go to Discover showing students with similar answers | Setup goes to Home; matching on answers not built |
| T6 Discovery Page | Refresh capability | Not built |
| T9 Private Messages | Send and view images/videos (links work as text) | Not built |

## Unit and API tests (pytest) — 147 tests

These call the Django API directly through DRF's test client (no browser), so
they're fast and cover edge cases the UI tests don't.

| App | File | Tests | What they cover |
| --- | --- | --- | --- |
| users | `users/tests/test_views.py` | 34 | Signup validation (.edu only, duplicates in any case, password rules, college required); verification links (tampered/foreign/old tokens rejected, link dies after first login); login/logout/me, token reuse and revocation, one generic error for bad credentials |
| profiles | `profiles/tests/test_views.py` | 51 | Create/update own profile; date of birth required, 18+ only, no future/impossible dates; gender choices; city; public profiles show age, never the birth date; tag cleaning and limits; links (http(s) only, max 5, https added); public profiles hide email and exclude yourself and unverified users; questionnaire answers (save, replace, invalid choice rejected, private); search/filter params incl. city, gender and age range (parametrized tables) |
| connections | `connections/tests/test_models.py` | 5 | One row per pair, no self-connections, status from each side |
| connections | `connections/tests/test_views.py` | 20 | Send/accept/decline/cancel/remove requests; privacy (others can't see your connections); declined senders can't resend |
| chat | `chat/tests/test_models.py` | 8 | One conversation per pair; only participants can send; no sending after disconnect; read receipts |
| chat | `chat/tests/test_views.py` | 17 | Starting a chat requires an accepted connection; chat list and unread counts; message history paging; blank/too-long messages rejected; rate limiting |
| chat | `chat/tests/test_consumers.py` | 12 | WebSocket chat: login required, only participants can join, other-site origins rejected, live delivery to both sides, invalid messages get errors, read receipts |
| **Total** | | **147** | |

## Totals

| Suite | Tests | Command |
| --- | --- | --- |
| Unit + API (pytest) | 147 | `pytest` |
| UI automation (Selenium) | 28 | `pytest tests_ui` |
| **All** | **175** | |
