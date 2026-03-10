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
- `Reservation`: links `CustomUser` → `Store` with `start_time`, `end_time`, `is_paid`, `status` (RESERVED/CHECKED_IN/CHECKED_OUT/CANCELLED), a UUID `qr_token` (auto-generated, immutable), and OTP fields (`otp_code`, `otp_expires_at`, `otp_is_used`) stored directly on the reservation row (no separate table).

**`config/`** — Project settings and root URL config. URL routing: `""` → `reservations.urls`, `"accounts/"` → `accounts.urls`.

**Settings behavior:**
- `DEBUG = True` locally; `False` when `RENDER` env var is set
- Database: SQLite3 by default; switches to PostgreSQL when `DATABASE_URL` env var is present (via `dj-database-url`)
- `AUTH_USER_MODEL = "accounts.CustomUser"` — must use `settings.AUTH_USER_MODEL` in FKs, not the model directly
- After login/logout, redirects to `reservations:store_list`
- Static files served via WhiteNoise in production; `STATIC_ROOT = staticfiles/`

**Deployment (Render):** `build.sh` runs `pip install -r requirements.txt`, `collectstatic`, and `migrate`. The `requirements.txt` is the production dependency list; `pyproject.toml`/`uv.lock` are for local development with uv.
