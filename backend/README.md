<div align="center">
<svg width="120" height="120" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
<path fill="#D92C2C" d="M50 0 C25 25, 25 50, 50 100 C75 50, 75 25, 50 0 Z" />
<rect x="42" y="28" width="16" height="44" rx="3" fill="white" />
<rect x="28" y="42" width="44" height="16" rx="3" fill="white" />
</svg>

# Virtual Blood Bank (VBB) - Backend API

**A Django & DRF backend to power life-saving mobile and web applications for healthcare professionals in Ethiopia.**

</div>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python">
  <img alt="Django" src="https://img.shields.io/badge/Django-5.0-092E20.svg?style=for-the-badge&logo=django">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=for-the-badge&logo=postgresql">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-24.0-2496ED.svg?style=for-the-badge&logo=docker">
</p>

---

## 📖 Overview

Welcome to the Virtual Blood Bank (VBB) project! This repository contains the backend API that drives the VBB mobile and web clients. Our goal is to create a reliable platform for healthcare workers in rural areas to manage blood inventory and request blood from nearby facilities, ultimately saving lives.

The API now includes a robust, **nested resource structure** and a **stateful blood request lifecycle**, enabling complex inter-facility coordination.

## 🧠 Project Philosophy & Key Concepts

If you're coming from a pure Django background, some parts of this project's structure might seem new. Here’s a quick rundown of the key tools and why we're using them.

### 1. Why Docker? (`Dockerfile`, `compose.yaml`)

*   **What it is:** Docker "containerizes" our application. It packages the Django code, the correct Python version, and all dependencies into a self-contained unit. The `compose.yaml` file defines and runs all our project's services (the Django app, the database) together.
*   **The Problem it Solves:** It eliminates "it works on my machine" issues. Everyone on the team runs the exact same environment, guaranteeing consistency between our development machines and the future production server.

### 2. Why a `Makefile`? (The Task Runner)

*   **What it is:** A `Makefile` is a simple "task runner." It lets us create short, memorable aliases (like `make setup` or `make lint`) for the long, complex commands we use for Docker.
*   **The Problem it Solves:** You don't have to remember or type `docker compose -f compose.yaml exec web python manage.py migrate`. You just type `make migrate`. It simplifies our entire workflow. **Run `make help` to see all available shortcuts!**

### 3. Why Split Settings? (`config/settings/`)

*   **What it is:** We've split Django's standard `settings.py` into three files:
    *   `base.py`: Contains all settings that are common to *every* environment (like `INSTALLED_APPS`).
    *   `dev.py`: Contains settings *only* for local development (like `DEBUG = True`). It imports everything from `base.py`.
    *   `prod.py`: Contains settings for the live production server (e.g., security settings).
*   **The Problem it Solves:** This is a best practice for security and maintainability. It prevents us from ever accidentally deploying our app to a live server with insecure development settings.

## 🛠️ Technology Stack

*   **Backend:** [Django](https://www.djangoproject.com/), [Django REST Framework](https://www.django-rest-framework.org/)
*   **Database:** [PostgreSQL](https://www.postgresql.org/)
*   **Authentication:** JWT via [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/) (login by email or phone); django-allauth retained for account/email-reset flows
*   **Push Notifications:** Firebase Cloud Messaging (free tier; no-ops without credentials)
*   **API Filtering:** [django-filter](https://django-filter.readthedocs.io/en/stable/)
*   **Containerization:** [Docker](https://www.docker.com/) & Docker Compose
*   **Static Files:** [WhiteNoise](https://whitenoise.readthedocs.io/) (served from the app container in production)
*   **Task Runner:** [GNU Make](https://www.gnu.org/software/make/)
*   **Configuration:** `django-environ`
*   **Code Quality:** linting, formatting, and tests run via `make lint`, `make format`, and `make test` (tool configuration lives in `pyproject.toml`)
*   **CI/CD:** GitHub Actions (lint + test + Docker build); deployable to [Render](https://render.com/)

## 📚 Documentation Structure

Project documentation is organized by purpose:

Documentation lives at the repository root (`../docs/`), shared across the
backend and the future mobile and web clients:

*   **Authoritative specs:** `../docs/SRS.pdf`, `../docs/SDS.pdf`
*   **API contract** (endpoints, payloads, auth, errors): [../docs/api/API.md](../docs/api/API.md)
*   **Domain Context:** [../docs/CONTEXT.md](../docs/CONTEXT.md)
*   **Architecture Decisions (ADRs):** `../docs/architecture/decisions/`
*   **Product Specs (SRS/SDS/Phases):** `../docs/product/`
*   **Runbooks (deploy, dispatcher, incidents):** `../docs/runbooks/`
*   **Documentation index:** `../docs/README.md`

## 🚀 Getting Started: A 5-Minute Setup

### Step 0: Install Prerequisites

Before you begin, ensure you have the following installed on your system:
*   **Git:** For cloning the repository.
*   **Docker Desktop:** This is the easiest way to get both Docker and Docker Compose. You can download it from the [**official Docker website**](https://www.docker.com/products/docker-desktop/).

### Installation Steps

1.  **Clone the Repository**
    ```sh
    git clone <your-repository-url>
    cd vbb_backend/backend   # the backend project lives in ./backend
    ```
    All commands below (`make ...`, `manage.py ...`) are run from `backend/`.

2.  **Create the Environment File**
    ```sh
    cp .env.example .env
    ```
    *(The default values are fine for local development.)*

3.  **Run the Automated Setup**
    This single command builds the Docker containers, starts the services, and runs initial migrations.
    ```sh
    make setup
    ```
    *(Optional: seed development data with `docker compose exec web python manage.py seed_dev_data`.)*

4.  **Create an Admin Superuser**
    You'll need an admin account to manage data via the Django Admin interface.
    ```sh
    make superuser
    ```

✅ **Setup Complete!** The application is now running.
*   **Testing UI (Login):** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
*   **Browsable API Root:** [http://127.0.0.1:8000/api/v1/](http://127.0.0.1:8000/api/v1/)
*   **Django Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 👤 User Flows for Testing

For development and testing, a simple login page is provided at the site root.
It is **not** the final frontend but is a handy tool for interacting with the
browsable API as an authenticated user.

**Note:** There is no self-service signup — accounts are provisioned by an
admin (via `POST /api/v1/users/`, which returns a temporary password, or via
`make superuser` / the Django admin). Newly provisioned users must change
their password on first login before other endpoints unlock.

### Login Flow

1.  **Navigate to Login:** Go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
2.  **Enter Credentials:** Use the email (or phone) and password of an active user.
3.  **Access API:** Upon successful login you can interact with the API
    according to your user's role and facility.

---

## 🗺️ API Endpoints

> Roles follow the three-role least-privilege matrix (ADR-0008): **SUPPLY** manages
> own-facility inventory and fulfills incoming requests (accept/reject/ship);
> **CLINICIAN** raises requests and confirms receipt (create/cancel/receive);
> **ADMIN** manages users/facilities and performs no clinical actions.

### Authentication

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login/` | Obtain a JWT pair (`username` accepts email or phone + `password`). |
| `POST` | `/api/v1/auth/refresh/` | Exchange a refresh token for a new access token. |
| `GET`/`PATCH` | `/api/v1/auth/me/` | View or update the authenticated user's profile. |
| `POST` | `/api/v1/auth/change-password/` | Change your password (required on first login). |

### Core Resources

| Method | Endpoint | Description | Permissions |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/` | Facility summary: inventory, requests, low-stock & expiring-soon alerts. | Authenticated |
| `GET` | `/api/v1/district-inventory/` | District-wide inventory (same woreda). Filter `?search=`, `?blood_type=`. | Authenticated |
| `GET` | `/api/v1/facilities/` | List facilities. | Authenticated (write: Admin) |
| `GET`/`POST` | `/api/v1/users/` | List / create users (create returns a temp password). | Admin Only |
| `POST` | `/api/v1/users/{id}/deactivate/` · `/reactivate/` · `/assign-role/` | Manage an account. | Admin Only |
| `GET` | `/api/v1/blood-requests/`| List requests. Filter `?status=`, `?blood_type=`, `?type=incoming`. | Authenticated |
| `POST`| `/api/v1/blood-requests/`| Create a request (accepts `notes`). | Clinician |
| `GET` | `/api/v1/donation-centers/` · `/nearby/?lat=&lng=` | Donor center directory; nearest-first. | Authenticated |
| `GET` | `/api/v1/notifications/` · `POST .../{id}/mark_read/` | List own notifications; mark read. | Authenticated |

### Nested Facility Resources

| Method | Endpoint | Description | Permissions |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/facilities/{id}/inventory/` | Blood units for a facility (flags `is_expiring_soon`). Filter `?blood_type=`. | Authenticated |
| `POST`| `/api/v1/facilities/{id}/inventory/` | Add a blood unit to your own facility. | Supply |
| `GET` | `/api/v1/facilities/{id}/inventory-summary/`| Aggregated unit counts by type. | Authenticated |
| `GET` | `/api/v1/facilities/{id}/staff/` | Users registered to a facility. | Admin Only |

### Blood Request Lifecycle Actions

These are `POST` requests that transition a blood request's state.

| Action | Endpoint | Description | Performed By |
| :--- | :--- | :--- | :--- |
| **Accept** | `/api/v1/blood-requests/{id}/accept/` | Approves a request and deducts units from inventory. | Supply, **fulfilling** facility |
| **Reject** | `/api/v1/blood-requests/{id}/reject/` | Denies a pending request (accepts `reason`). | Supply, **fulfilling** facility |
| **Ship** | `/api/v1/blood-requests/{id}/ship/` | Marks the accepted units in-transit. | Supply, **fulfilling** facility |
| **Receive**| `/api/v1/blood-requests/{id}/receive/`| Confirms receipt and adds units to the requesting facility. | Clinician, **requesting** facility |
| **Cancel** | `/api/v1/blood-requests/{id}/cancel/` | Cancels a PENDING or ACCEPTED request (restores reserved stock). | Clinician, **requesting** facility |

---

## ⚙️ Daily Development Workflow

Use these `make` commands to manage your environment. **Run `make help` for a full list.**

### Environment Management
| Command | Description |
| :--- | :--- |
| `make up` | 🚀 Starts the Django and DB containers in the background. |
| `make down` | 🛑 Stops all running services. |
| `make logs` | 📜 Shows the real-time logs from the Django server. (Press `Ctrl+C` to exit). |
| `make down-vol` | 💥 **(Destructive!)** Stops services and deletes the database volume. |

### Code Quality & Database
| Command | Description |
| :--- | :--- |
| `make format` | 🎨 Auto-formats all Python code. |
| `make lint` | 🔎 Checks for linting and formatting issues. |
| `make test` | 🧪 Runs the test suite. |
| `make migrate` | 🏃 Runs any pending database migrations. |
| `make superuser`| 👑 Creates a new Django superuser account. |
| `make shell` | 💻 Opens an interactive shell inside the Django container. |

## 📁 Project Structure

The repository is a monorepo. This backend lives in `backend/`; product/architecture
documentation is at the repo root in `docs/`; the mobile and web clients will live
in `mobile/` and `web/`.

```
<repo root>/
├── backend/                    # ← this Django project
│   ├── apps/                   # Django apps (application code)
│   │   ├── core/               #   Shared validators + the password-change gate
│   │   ├── users/              #   User & Facility models, JWT auth, user management
│   │   ├── inventory/          #   BloodUnit & BloodRequest
│   │   │   ├── api/            #     HTTP layer: serializers, views, urls, filters
│   │   │   ├── domain/         #     Business logic: lifecycle, transitions,
│   │   │   │                   #       authorizers, dashboard service
│   │   │   └── config.py       #     Centralized domain constants (see ../docs/CONTEXT.md)
│   │   ├── notifications/      #   Async notification events + FCM delivery
│   │   ├── donations/          #   Donation-center directory + nearest-by-distance
│   │   └── audit/              #   Immutable audit log
│   ├── config/                 # Project config: settings/{base,dev,prod}.py, urls, wsgi
│   ├── scripts/                # start.sh (prod entrypoint), lint.sh, format.sh
│   ├── templates/              # HTML template for the login test page
│   ├── compose.yaml            # Local dev services (web, db, lint, test)
│   ├── Dockerfile              # Multi-stage build (base / dev / prod)
│   ├── Makefile                # Dev workflow shortcuts (run `make help`)
│   ├── pyproject.toml          # Dependencies + tool config
│   └── README.md               # You are here!
├── docs/                       # Documentation (see docs/README.md)
│   ├── SRS.pdf, SDS.pdf        #   Authoritative specifications
│   ├── architecture/decisions/ #   ADRs
│   ├── runbooks/               #   Operational runbooks
│   └── product/                #   SRS/SDS summaries, delivery phases
├── render.yaml                 # Render deployment blueprint (points to ./backend)
└── README.md                   # Monorepo overview
```

---

## 🏛️ Architecture

Each app separates its **HTTP layer** from its **business logic**:

*   **`api/`** — DRF serializers, viewsets, routing, and filters. This is the thin
    edge that translates HTTP to and from domain operations.
*   **`domain/`** — pure business logic with no DRF/HTTP concerns: the blood-request
    **lifecycle state machine**, allowed **transitions**, **authorizers** (who may
    perform an action), and the **dashboard** aggregation service.

This keeps domain rules unit-testable in isolation and prevents view code from
accumulating business logic.

**Key flows:**

*   **Blood Request Lifecycle** — a request moves through an explicit state machine
    (pending → accepted/rejected → shipped → received, or cancelled). Transitions are
    only permitted from valid states and by authorized facilities. See
    [ADR-0001](../docs/architecture/decisions/ADR-0001-blood-request-transitions.md).
*   **Notifications** — domain events are persisted, then the dispatcher
    (`manage.py dispatch_notifications`, either as a `--loop` worker or scheduled
    one-shot runs) fans each event out to the FCM push channel
    asynchronously, without a broker. See
    [ADR-0002](../docs/architecture/decisions/ADR-0002-async-notification-dispatch-without-celery.md),
    [ADR-0007](../docs/architecture/decisions/ADR-0007-fcm-push-drop-sms.md), and the
    [dispatcher runbook](../docs/runbooks/notification-dispatcher.md). The separate
    `manage.py remove_expired_blood` command purges expired inventory; it has no
    worker mode and is meant to run as a daily cron (the notification worker does
    not cover it).
*   **Domain configuration** — clinical/business constants (blood types, expiry days,
    low-stock threshold, woreda range, page size) are centralized in
    `apps/inventory/config.py` and overridable via env. See [../docs/CONTEXT.md](../docs/CONTEXT.md).

---

## ☁️ Deployment (Render)

Production runs the **`prod` stage** of the multi-stage `Dockerfile` — no Docker
Compose. Configuration is entirely env-driven via `config.settings.prod`.

1.  Push the repo to GitHub and create a new **Blueprint** on Render pointing at
    [`render.yaml`](../render.yaml). It provisions the web service + a managed
    PostgreSQL 16 database.
2.  `SECRET_KEY` is generated by Render; `DATABASE_URL` is wired from the database;
    `RENDER_EXTERNAL_HOSTNAME` is injected and automatically added to
    `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`.
3.  On each deploy, `scripts/start.sh` runs migrations and then serves the app with
    Gunicorn on `$PORT`. Static files are collected at image-build time and served by
    WhiteNoise.
4.  Health checks hit `GET /healthz/`.

For the full operational procedure (env vars, rollback, troubleshooting), see
the [deploy runbook](../docs/runbooks/deploy.md).

To build the production image locally:

```sh
docker build --target prod -t vbb-backend .
```

The settings are validated with Django's deployment checklist:

```sh
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py check --deploy
```

---

## 🤝 Contributing

Contributions are welcome! Please follow the standard GitHub Flow:
1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.
