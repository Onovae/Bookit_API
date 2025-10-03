# BookIt API

Production-ready REST API that powers a lightweight bookings platform. It embraces FastAPI for speed, PostgreSQL for reliability, and JWT for secure authentication.

---

## Contents

1. [Overview](#overview)
2. [Architecture & Stack](#architecture--stack)
3. [Why PostgreSQL](#why-postgresql)
4. [Domain Model](#domain-model)
5. [Feature Highlights](#feature-highlights)
6. [Project Layout](#project-layout)
7. [Configuration](#configuration)
8. [Local Development](#local-development)
9. [Database & Migrations](#database--migrations)
10. [Testing](#testing)
11. [API Surface](#api-surface)
12. [Deployment (Render)](#deployment-render)
13. [Acceptance Checklist](#acceptance-checklist)
14. [Future Enhancements](#future-enhancements)

---

## Overview

BookIt lets customers browse services, schedule appointments, and review their experience. Admins manage the service catalogue and oversee bookings. The backend is modular, testable, and ready for deployment on Render or any container-friendly host.

## Architecture & Stack

- **FastAPI** for high-performance Python APIs with automatic OpenAPI docs.
- **PostgreSQL** for relational storage with UUID primary keys.
- **SQLAlchemy + Alembic** handle ORM mapping and migrations.
- **Pydantic v2** enforces request/response validation.
- **JWT + bcrypt** secure authentication and password storage.
- **Uvicorn** ASGI server (reload for dev, single worker for production simplicity).
- **Pytest** for automated regression tests.
- **Structured logging** based on environment configuration.

## Why PostgreSQL

- Built-in `UUID` column type keeps IDs consistent with our domain model.
- Rich constraint support (FK, enum, unique) matches business rules.
- Works seamlessly with Alembic migration workflow.
- Familiar operational tooling for deployment hosts (backup, scaling, managed instances).

## Domain Model

| Entity      | Key Fields                                                                           | Notes                                                    |
| ----------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| **User**    | `id`, `name`, `email`, `password_hash`, `role`, `created_at`                         | `role` is `user` or `admin`; email unique.               |
| **Service** | `id`, `title`, `description`, `price`, `duration_minutes`, `is_active`, `created_at` | Inactive services hidden from public queries.            |
| **Booking** | `id`, `user_id`, `service_id`, `start_time`, `end_time`, `status`, `created_at`      | Conflict detection prevents overlapping active bookings. |
| **Review**  | `id`, `booking_id`, `rating`, `comment`, `created_at`                                | One review per completed booking, owned by booking user. |

## Feature Highlights

- **Authentication** – Register, login, refresh, logout with JWT tokens; passwords hashed via bcrypt.
- **Authorization** – Role-aware dependency graph: users can only touch their records; admins access management routes.
- **Booking workflow** – Validates future-dated requests, enforces service duration, blocks overlaps, and supports status changes.
- **Reviews** – Only possible after a booking is marked `completed`; duplicate reviews blocked.
- **Observability** – Settings-driven logging level, request logging from Uvicorn/Starlette.
- **Test Fixtures** – SQLite-backed fixtures mirror PostgreSQL UUID behaviour for speedy tests.

## Project Layout

```
app/
  api/           # APIRouter modules (auth, users, services, bookings, reviews, health)
  services/      # Business logic and validation orchestration
  schemas/       # Pydantic models for requests/responses
  models/        # SQLAlchemy ORM models (PostgreSQL-backed)
  core/          # Security, JWT helpers, config loading
  config/        # Settings and database session management
alembic/         # Migration environment + revision history
tests/           # Pytest suite with fixtures and scenario coverage
scripts/         # (root) Helper scripts like create_admin.py, recreate_db.py
```

## Configuration

Environment variables power secrets and deployment-specific settings. Copy `.env.example` to `.env` and adjust.

| Key                           | Description                            | Example                                               |
| ----------------------------- | -------------------------------------- | ----------------------------------------------------- |
| `DATABASE_URL`                | PostgreSQL connection string           | `postgresql://postgres:pass@localhost:5432/bookit_db` |
| `SECRET_KEY`                  | JWT signing secret (>=32 chars)        | `generate-a-long-random-string`                       |
| `ALGORITHM`                   | JWT algorithm                          | `HS256`                                               |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime                  | `30`                                                  |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token lifetime                 | `7`                                                   |
| `ENVIRONMENT`                 | `development`, `staging`, `production` | `development`                                         |
| `DEBUG`                       | Toggle debug features                  | `True`                                                |
| `LOG_LEVEL`                   | Python logging level                   | `INFO`                                                |
| `ADMIN_EMAIL`                 | Seed admin email                       | `admin@example.com`                                   |
| `ADMIN_PASSWORD`              | Seed admin password                    | `AdminBookIt2024!`                                    |
| `ADMIN_NAME`                  | Seed admin display name                | `System Administrator`                                |

> Secrets should never be committed; rely on platform-specific secret managers in production.

## Local Development

1. **Create virtualenv**

   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

   (macOS/Linux: `source venv/bin/activate`)

2. **Install dependencies**

   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Provision database**

   ```powershell
   psql -c "CREATE DATABASE bookit_db;"
   ```

4. **Set environment** – duplicate `.env.example` to `.env` and fill values.

5. **Apply migrations**

   ```powershell
   alembic upgrade head
   ```

6. **(Optional) seed admin**

   ```powershell
   python create_admin.py
   ```

7. **Run the API**

   ```powershell
   uvicorn app.main:app --reload
   ```

8. **Explore docs** – visit `http://127.0.0.1:8000/docs` (Swagger) or `/redoc`.

## Database & Migrations

- New schema changes are tracked through Alembic revisions under `alembic/versions`.
- Generate a revision after editing models:
  ```powershell
  alembic revision --autogenerate -m "Describe change"
  alembic upgrade head
  ```
- `recreate_db.py` is available for local PostgreSQL resets (drops & recreates). Use with caution.

## Testing

Run the full suite:

```powershell
pytest -vv
```

Test coverage includes:

- Auth: register/login/refresh/401/403 paths.
- Booking lifecycle: success path, overlap conflicts (`409`), invalid times (`422`).
- Permissions: user vs admin access to services/bookings.
- Review constraints: ensures rule of one review per completed booking.

Fixtures in `tests/conftest.py` mirror production behaviour (UUID support, hashed passwords, unique emails) to keep tests close to reality.

## API Surface

All routes are under `/api/v1`. Selected highlights:

| Area     | Endpoint         | Method       | Role                        | Notes                                                    |
| -------- | ---------------- | ------------ | --------------------------- | -------------------------------------------------------- |
| Auth     | `/auth/register` | POST         | Public                      | Creates new user, returns profile                        |
| Auth     | `/auth/login`    | POST         | Public                      | Returns access + refresh tokens                          |
| Auth     | `/auth/refresh`  | POST         | Public (with refresh token) | Issues new access token                                  |
| Auth     | `/auth/logout`   | POST         | Authenticated               | Simple token revoke hook                                 |
| Users    | `/users/me`      | GET/PATCH    | Authenticated               | View/update own profile                                  |
| Services | `/services`      | GET          | Public                      | Supports `q`, `price_min`, `price_max`, `active` filters |
| Services | `/services`      | POST         | Admin                       | Create service                                           |
| Services | `/services/{id}` | PATCH/DELETE | Admin                       | Update or archive service                                |
| Bookings | `/bookings`      | POST         | User                        | Enforces future start, duration, conflict rules          |
| Bookings | `/bookings`      | GET          | User/Admin                  | Users see theirs; admins can filter all                  |
| Bookings | `/bookings/{id}` | PATCH        | User/Admin                  | User reschedule/cancel, admin update status              |
| Reviews  | `/reviews`       | POST         | User                        | Only for completed bookings, one per booking             |
| Reviews  | `/reviews/{id}`  | PATCH/DELETE | Owner/Admin                 | Manage review content                                    |
| Health   | `/health`        | GET          | Public                      | Simple readiness probe                                   |

Every protected route expects `Authorization: Bearer <access_token>` header.

## Deployment (Render)

1. **Push to GitHub** – repository was linked by Render.
2. **Provision PostgreSQL** – managed Render PostgreSQL instance and note URL/credentials.
3. **Create Web Service**
   - Build command: _(none required)_
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
   - Environment: set variables from `.env` (used Render Secrets manager).
4. **Run migrations** – open Render shell and execute `alembic upgrade head`.
5. **Seed admin** – run `python create_admin.py` once.
6. **Expose docs** – once live, add:
   - Production base URL (`https://bookit-api-d84x.onrender.com`)
   - Swagger docs link (`https://bookit-api-d84x.onrender.com/docs`)
7. **Monitoring** – rely on Render logs; consider adding structured log shipping later.

**admin login**
Admin Email: maureenonovae593@gmail.com
password: AdminBookIt2024!

## Acceptance Checklist

- [x] Can register/login and access protected routes with JWT.
- [x] Admin-only routes enforce 401/403 for regular users.
- [x] Booking conflict detection returns 409 Conflict.
- [x] HTTP methods/status codes match REST expectations across endpoints.
- [x] Modular separation of routers, services, repositories, schemas.
- [x] Pytest suite covers auth, permissions, booking logic.
- [x] Documentation updated with setup, env explanation, deployment plan.
- [ ] Add production URL + `/docs` link after Render deployment.

## Future Enhancements

- Add email notifications or calendar integrations for bookings.
- Implement pagination and sorting on list endpoints.
- Introduce background jobs for stale booking cleanup.
- Plug in metrics/monitoring (OpenTelemetry, Prometheus) for production observability.
- Add email verification and OTP flow using SMTP provider credentials (e.g. Google App Password) to harden account access once deployed.
