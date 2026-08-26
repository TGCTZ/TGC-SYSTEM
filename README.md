# TGC-SYSTEM

A Django rebuild of the TGC gemmological workflow system — order reception,
identification/findings, production (sonara, carving, lapidary), certificates,
and GePG billing — engineered from the ground up on clean architecture and
strict conventions.

---

## Documentation

| Document | What it covers |
| --- | --- |
| [`docs/conventions.md`](docs/conventions.md) | Django & Python coding standards — architecture rules, models, views/services, security, testing, and the pre-commit checklist. |
| [`docs/project-structure.md`](docs/project-structure.md) | The annotated folder layout — the purpose of every folder and file. |

> New to the codebase? Read `project-structure.md` first to learn *where things
> live*, then `conventions.md` for *how we write code here*.

---

## Getting started

> Setup steps will be filled in as the project is scaffolded.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements/development.txt

# 3. Configure environment
cp .env.example .env             # then edit values

# 4. Apply migrations and run
python manage.py migrate
python manage.py runserver
```

---

## Tech stack

- **Python** · **Django 5**
- **PostgreSQL**
- **Ruff** (lint + format) · **pytest** (tests) · **factory_boy** (test data & seeding)

---

## Project status

Early scaffolding. Architecture and conventions are defined; application code is
being built out. See the documentation above.
