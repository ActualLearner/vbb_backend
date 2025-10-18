<div align="center">

<img src="https://user-images.githubusercontent.com/835384/201221132-243550bb-d68f-4809-9b4a-a111a1d2932b.png" alt="Logo" width="120" height="120">

# Virtual Blood Bank (VBB) - Backend API

**A Django & DRF backend to power a life-saving mobile application for healthcare professionals in Ethiopia.**

</div>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python">
  <img alt="Django" src="https://img.shields.io/badge/Django-5.0-092E20.svg?style=for-the-badge&logo=django">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=for-the-badge&logo=postgresql">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-24.0-2496ED.svg?style=for-the-badge&logo=docker">
</p>

---

## 📖 Overview

Welcome to the Virtual Blood Bank (VBB) project! This repository contains the backend API that drives the VBB mobile app. Our goal is to create a reliable platform for healthcare workers in rural areas to manage blood inventory and request blood from nearby facilities, ultimately saving lives.

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
*   **Authentication:** [django-allauth](https://django-allauth.readthedocs.io/en/latest/) (Headless API for Session Auth)
*   **Containerization:** [Docker](https://www.docker.com/) & Docker Compose
*   **Task Runner:** [GNU Make](https://www.gnu.org/software/make/)
*   **Configuration:** `django-environ`
*   **Code Quality:** `flake8` (Linting), `black` (Formatting), `isort` (Import Sorting)

## 🚀 Getting Started: A 5-Minute Setup

### Step 0: Install Prerequisites

Before you begin, ensure you have the following installed on your system:
*   **Git:** For cloning the repository.
*   **Docker Desktop:** This is the easiest way to get both Docker and Docker Compose. You can download it from the [**official Docker website**](https://www.docker.com/products/docker-desktop/).

### Installation Steps

1.  **Clone the Repository**
    ```sh
    git clone <your-repository-url>
    cd vbb_project
    ```

2.  **Create the Environment File**
    ```sh
    cp .env.example .env
    ```
    *(The default values are fine for local development.)*

3.  **Run the Automated Setup**
    This single command builds the Docker containers, starts the services, and runs initial migrations and data seeding.
    ```sh
    make setup
    ```

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

For development and testing, simple login and signup pages are provided. These are **not** the final frontend but are essential tools for interacting with the browsable API as an authenticated user.

**Note:** For ease of local development, email verification and manual admin approval are currently disabled. A new user is **active immediately** upon signup.

### New User Signup Flow

1.  **Navigate to Signup:** Go to [http://127.0.0.1:8000/signup/](http://127.0.0.1:8000/signup/).
2.  **Fill the Form:** Enter a username, email, password, and select a facility from the dropdown.
3.  **Login:** Upon successful submission, the account is created and is immediately active. You can now proceed directly to the login page.

### Existing User Login Flow

1.  **Navigate to Login:** Go to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
2.  **Enter Credentials:** Use the email and password of an active user.
3.  **Access API:** Upon successful login, you are redirected to the browsable API root. Your browser session is now authenticated, and you can interact with the API according to your user's permissions.

---

## 🗺️ API Endpoints

### Top-Level Resources

| Method | Endpoint | Description | Permissions |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/facilities/` | Get a list of all health facilities. | Authenticated |
| `GET` | `/api/v1/users/` | Get a list of all users. | Admin Only |
| `GET` | `/api/v1/blood-requests/`| Get a list of all blood requests in the system. | Authenticated |
| `POST`| `/api/v1/blood-requests/`| Create a new blood request. | Authenticated |

### Nested Facility Resources

| Method | Endpoint | Description | Permissions |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/facilities/{id}/inventory/` | Get blood units for a specific facility. Supports filtering by `?blood_type=`. | Authenticated |
| `POST`| `/api/v1/facilities/{id}/inventory/` | Add a new blood unit to a facility's inventory. | Facility Representative |
| `GET` | `/api/v1/facilities/{id}/inventory-summary/`| Get an aggregated count of blood units by type for a facility. | Authenticated |
| `GET` | `/api/v1/facilities/{id}/staff/` | Get a list of all users registered to a specific facility. | Authenticated |

### Blood Request Lifecycle Actions

These are `POST` requests made to specific URLs to transition the state of a blood request.

| Action | Endpoint | Description | Performed By |
| :--- | :--- | :--- | :--- |
| **Accept** | `/api/v1/blood-requests/{id}/accept/` | Approves a request and deducts blood units from inventory. | User from **fulfilling** facility |
| **Reject** | `/api/v1/blood-requests/{id}/reject/` | Denies a pending request. | User from **fulfilling** facility |
| **Ship** | `/api/v1/blood-requests/{id}/ship/` | Marks the accepted units as in-transit. | User from **fulfilling** facility |
| **Receive**| `/api/v1/blood-requests/{id}/receive/`| Confirms receipt and adds units to the requesting facility's inventory. | User from **requesting** facility |
| **Cancel** | `/api/v1/blood-requests/{id}/cancel/` | Cancels a request that has not yet been accepted. | User from **requesting** facility |

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
| `make format` | 🎨 Auto-formats all Python code with `black` and `isort`. |
| `make migrate` | 🏃 Runs any pending database migrations. |
| `make superuser`| 👑 Creates a new Django superuser account. |
| `make shell` | 💻 Opens an interactive shell inside the Django container. |

## 📁 Project Structure

```
vbb_project/
├── .flake8               # Configuration file for the flake8 linter
├── pyproject.toml        # Configuration for tools like black and isort
├── .env                  # Environment variables (GIT IGNORED)
├── apps/                 # Location for all Django apps (our code)
│   ├── users/            # Handles User, Facility models, auth forms
│   └── inventory/        # Handles BloodUnit, BloodRequest models, API logic
├── config/               # Project-level configuration
│   ├── settings/         # Split settings files (base.py, dev.py, prod.py)
│   ├── urls.py           # Root URL configuration
│   └── ...
├── templates/            # HTML templates for login/signup test pages
├── compose.yaml          # Defines our services (web, db, etc.) for Docker
├── Dockerfile            # Blueprint for building our Django container
├── Makefile              # Shortcuts for our development commands
├── requirements.txt      # List of Python dependencies
└── README.md             # You are here!
```

---

## 🤝 Contributing

Contributions are welcome! Please follow the standard GitHub Flow:
1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add some amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.
