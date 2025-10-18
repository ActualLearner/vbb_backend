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

This document will guide you through the project's structure, the tools we use, and how to get everything running smoothly.

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
*   **Containerization:** [Docker](https://www.docker.com/) & Docker Compose
*   **Task Runner:** [GNU Make](https://www.gnu.org/software/make/)
*   **Configuration:** `django-environ`
*   **Code Quality:** `flake8` (Linting), `black` (Formatting), `isort` (Import Sorting)

## 🚀 Getting Started: A 5-Minute Setup

Follow these steps to get the project running on your local machine.

### Prerequisites

*   You must have **Docker** and **Docker Compose** installed.
*   You must have `git` installed.

### Installation

1.  **Clone the Repository**
    ```sh
    git clone <your-repository-url>
    cd vbb_project
    ```

2.  **Create the Environment File**
    This file holds our secret keys and database credentials. It's ignored by Git for security.
    ```sh
    cp .env.example .env
    ```
    *(The default values in the `.env` file are fine for local development, so you don't need to change them.)*

3.  **Run the Automated Setup Command**
    This single command uses our `Makefile` to build the Docker containers, start the services, and run the initial database migrations.
    ```sh
    make setup
    ```

4.  **Create a Superuser**
    You'll need an admin account to access the Django Admin interface.
    ```sh
    make superuser
    ```
    Follow the prompts to set your username, email, and password.

✅ **Setup Complete!** The application is now running in the background.
*   **Browsable API:** [http://127.0.0.1:8000/api/v1/](http://127.0.0.1:8000/api/v1/)
*   **Django Admin:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## ⚙️ Daily Development Workflow

Use these `make` commands to manage your development environment. **Run `make help` for a full list of commands and their descriptions.**

### Environment Management
| Command | Description |
| :--- | :--- |
| `make up` | 🚀 Starts the Django and DB containers in the background. |
| `make down` | 🛑 Stops all running services. |
| `make logs` | 📜 Shows the real-time logs from the Django server. (Press `Ctrl+C` to exit). |
| `make down-vol` | 💥 **(Destructive!)** Stops services and deletes the database volume. |

### Code Quality
| Command | Description |
| :--- | :--- |
| `make format` | 🎨 Auto-formats all Python code with `black` and `isort`. |
| `make lint` | 🔎 Checks your code for style issues and errors with `flake8`. |
| `make qa` | ✅ Runs all quality checks (linting and tests). |

### Database & Django Commands
| Command | Description |
| :--- | :--- |
| `make migrate` | 🏃 Runs any pending database migrations. |
| `make superuser`| 👑 Creates a new Django superuser account. |
| `make shell` | 💻 Opens an interactive shell inside the Django container. |
| `make test` | 🧪 Runs the project's test suite. |

> **Example Workflow:** If you change a model in `apps/inventory/models.py`, you would:
> 1.  Run `docker compose exec web python manage.py makemigrations inventory` (This is one command not in the `Makefile` as it needs the app name).
> 2.  Run `make migrate` to apply the new migration.

## 📁 Project Structure

```
vbb_project/
├── .env                  # Environment variables (GIT IGNORED)
├── .flake8               # Configuration file for the flake8 linter
├── apps/                 # Location for all Django apps (our code)
│   ├── users/            # Handles User, Facility models and authentication
│   └── inventory/        # Handles BloodUnit and BloodRequest models
├── config/               # Project-level configuration (the "main" app)
│   ├── settings/         # Split settings files (base.py, dev.py, prod.py)
│   ├── urls.py           # Root URL configuration
│   └── ...
├── scripts/              # Helper shell scripts used by the Makefile
├── compose.yaml          # Defines our services (web, db, etc.) for Docker
├── Dockerfile            # Blueprint for building our Django container
├── Makefile              # Shortcuts for our development commands
├── manage.py             # Django's command-line utility
├── pyproject.toml        # Configuration for tools like black and isort
├── requirements.txt      # List of Python dependencies for pip
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
