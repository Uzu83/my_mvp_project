# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

省人化店舗運営システム (Store Operations Automation System) MVP — a Django app for managing store reservations with QR token-based check-in. Live at https://my-mvp-app-w6x2.onrender.com.

## Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run python manage.py runserver

# Run all tests
uv run python manage.py test

# Run tests for a specific app
uv run python manage.py test reservations
uv run python manage.py test accounts

# Run a single test
uv run python manage.py test reservations.tests.StoreModelTest.test_store_creation

# Apply migrations
uv run python manage.py migrate

# Create migrations after model changes
uv run python manage.py makemigrations

# Open Django shell
uv run python manage.py shell
```

## Architecture

Django 6.0 / Python 3.12 project with two apps:

**`accounts/`** — Custom user model extending `AbstractUser` with a `phone_number` field. Handles signup (auto-login on success), login, and logout. Django's built-in auth views handle login/logout; only signup has a custom view.

**`reservations/`** — Core business logic. Two models:
- `Store`: name + capacity
- `Reservation`: links `CustomUser` → `Store` with `start_time`, `end_time`, `is_paid`, `status` (RESERVED/CHECKED_IN/CHECKED_OUT/CANCELLED), a UUID `qr_token` (auto-generated, immutable), and OTP fields (`otp_code`, `otp_expires_at`, `otp_is_used`, `otp_failure_count`) stored directly on the reservation row (no separate table).

**`config/`** — Project settings and root URL config. URL routing: `""` → `reservations.urls`, `"accounts/"` → `accounts.urls`.

**Settings behavior:**
- `DEBUG = True` locally; `False` when `RENDER` env var is set
- Database: SQLite3 by default; switches to PostgreSQL when `DATABASE_URL` env var is present (via `dj-database-url`)
- `AUTH_USER_MODEL = "accounts.CustomUser"` — must use `settings.AUTH_USER_MODEL` in FKs, not the model directly
- After login/logout, redirects to `reservations:store_list`
- Static files served via WhiteNoise in production; `STATIC_ROOT = staticfiles/`

**Deployment (Render):** `build.sh` runs `pip install -r requirements.txt`, `collectstatic`, and `migrate`. The `requirements.txt` is the production dependency list; `pyproject.toml`/`uv.lock` are for local development with uv.

**Tech Stack additions:**
- `qrcode`, `pillow` — QR code generation (added via `uv add`; sync `requirements.txt` with `uv pip freeze > requirements.txt` after adding)

## Coding Patterns

**QR code generation:**
- Always generate QR images in memory using `io.BytesIO`; never save to disk.
- Embed as Base64 in templates: `<img src="data:image/png;base64,{{ qr_b64 }}">`.
- Use the shared helper in `reservations/views.py`:
  ```python
  def generate_qr_base64(qr_token):
      img = qrcode.make(str(qr_token))
      buffer = io.BytesIO()
      img.save(buffer, format="PNG")
      return base64.b64encode(buffer.getvalue()).decode()
  ```

## Security Rules

These rules are non-negotiable. Any code that violates them must be rejected regardless of other considerations.

**Timing-safe comparison — always use `hmac.compare_digest`**
- When comparing secrets (OTP codes, tokens, passwords), NEVER use `==`. Use `hmac.compare_digest(a, b)` exclusively.
- `==` short-circuits on the first mismatch, leaking timing information that an attacker can exploit to enumerate valid codes character by character.

**Cryptographic randomness — always use `secrets`**
- Use `secrets.randbelow(n)` for OTP generation. NEVER use `random.randint` or similar non-cryptographic PRNGs.

**Preventing IDOR (Insecure Direct Object Reference)**
- All views that fetch a specific `Reservation` must include `user=request.user` in the lookup:
  ```python
  get_object_or_404(Reservation, pk=pk, user=request.user)
  ```
- Omitting this check allows any authenticated user to access or modify another user's data by guessing a PK.

**Atomic DB operations with row-level locking**
- Whenever updating a row based on its current state (e.g., OTP check-in, failure count increment), ALWAYS use `transaction.atomic()` + `select_for_update()` together:
  ```python
  with transaction.atomic():
      reservation = Reservation.objects.select_for_update().get(pk=pk, user=request.user)
      # ... read-then-write logic here
  ```
- `select_for_update()` alone without `atomic()` has no effect. Using `atomic()` alone without `select_for_update()` does not prevent concurrent reads from seeing stale state.
- Note: `select_for_update()` degrades to a table lock on SQLite. Use PostgreSQL for accurate behavior in tests.

**Brute-force protection**
- Never call the secret comparison before checking `otp_failure_count >= 5`. Locking out must happen before the comparison, not after.
- Format-invalid inputs (non-6-digit strings) must be rejected before entering the DB transaction. This prevents an attacker from burning lockout budget without having a valid-format guess.

## Testing Rules

**Test file layout**
- Tests live in `reservations/tests/` as a package with an `__init__.py`.
- Business logic tests: `test_models.py`. OTP and security tests: `test_otp.py`.
- Do not put tests in `tests.py` at the app root — this conflicts with the `tests/` package.

**PostgreSQL is required for OTP tests**
- `select_for_update()` behavior is only accurate under PostgreSQL. Run OTP tests with:
  ```bash
  DATABASE_URL=postgres://postgres:postgres@localhost:5432/test_db \
    uv run python manage.py test reservations.tests.test_otp --settings=config.test_settings
  ```
- CI runs all tests against PostgreSQL via the `postgres:15` service container. See `.github/workflows/ci.yml`.

**Test naming convention**
- Test method names must describe the expected outcome, not just the operation:
  - ✅ `test_lockout_after_5_failures`
  - ✅ `test_expired_otp_fails`
  - ❌ `test_otp_verify`

**Use `force_login` for auth in tests**
- Always use `self.client.force_login(user)` instead of `self.client.login(username=..., password=...)` to avoid coupling tests to the authentication backend.

## Regex Rules

**Always use raw strings for regex patterns**
- ALWAYS write `r"\d{6}"` not `"\\d{6}"`. The raw-string prefix `r` prevents Python from interpreting backslashes before the regex engine sees the pattern.
- In this project, the canonical 6-digit OTP pattern is `r"\d{6}"`. Use `re.fullmatch(r"\d{6}", user_input)` — not `re.match`, which does not anchor the end of the string.

## Branch Naming Conventions（ブランチ命名規則）

ブランチ名は必ず以下のプレフィックスを使用してください。

- `feature/◯◯` — 新機能の開発（例: `feature/otp-checkin`）
- `fix/◯◯` — バグ修正（例: `fix/otp-lockout-count`）
- `docs/◯◯` — ドキュメントの更新（例: `docs/claude-md-branch-rules`）

## Custom Commands

- `/commit` — Create a git commit in Conventional Commits format automatically.
