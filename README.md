# TGC-SYSTEM

A Django rebuild of the TGC gemmological workflow system — order reception,
identification/findings, production (sonara, carving, lapidary), certificates,
and GePG billing — engineered from the ground up on clean architecture and
strict conventions.

---

## Documentation

See [`docs/README.md`](docs/README.md) for the full index. Highlights:

**Engineering** — how we build
| Document | What it covers |
| --- | --- |
| [`engineering/conventions.md`](docs/engineering/conventions.md) | Django & Python coding standards — architecture, models, services, security, testing. |
| [`engineering/project-structure.md`](docs/engineering/project-structure.md) | The annotated folder layout — the purpose of every folder and file. |

**Domain** — what we're building
| Document | What it covers |
| --- | --- |
| [`domain/business-workflow.md`](docs/domain/business-workflow.md) | End-to-end process: stages, roles, and the stone status lifecycle. |
| [`domain/domain-questions.md`](docs/domain/domain-questions.md) | Business decisions — settled and still open — that drive the data model. |

> New to the codebase? Read `project-structure.md` to learn *where things live*,
> `conventions.md` for *how we write code*, then the domain docs for *what the
> system does*.

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
