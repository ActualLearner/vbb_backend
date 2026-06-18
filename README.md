# Virtual Blood Bank (VBB)

A district-level mHealth system that helps rural Ethiopian health facilities share
blood in real time to reduce maternal mortality from postpartum hemorrhage. The
product has two components:

| Path | Component | Status |
| :--- | :--- | :--- |
| [`backend/`](backend/) | Django REST API (inventory, blood requests, auth, notifications) | ✅ Implemented |
| `mobile/` | Cross-platform mobile client (React Native / Flutter) | 🚧 Planned |

## Repository layout

```
backend/   # Django + DRF API — see backend/README.md to run it
mobile/    # Mobile client (future)
docs/      # Product & architecture docs (authoritative SRS.pdf / SDS.pdf, ADRs)
render.yaml  # Deployment blueprint (builds ./backend)
```

## Getting started

The backend is self-contained. To run it:

```sh
cd backend
cp .env.example .env
make setup
```

See [`backend/README.md`](backend/README.md) for full setup, API reference, and
architecture notes, and [`docs/README.md`](docs/README.md) for the specifications.

## Documentation

- **Authoritative specs:** [`docs/SRS.pdf`](docs/SRS.pdf), [`docs/SDS.pdf`](docs/SDS.pdf)
- **Domain context:** [`docs/CONTEXT.md`](docs/CONTEXT.md)
- **Architecture decisions:** [`docs/architecture/decisions/`](docs/architecture/decisions/)
