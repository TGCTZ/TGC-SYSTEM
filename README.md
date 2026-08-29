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

**Prerequisites:** Python 3.13, PostgreSQL, and Node.js + npm.

### First-time setup

```bash
# 1. Python environment
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements/development.txt

# 2. Front-end dependencies
npm install

# 3. Configuration — copy the template, then set a real SECRET_KEY and DB_* values
cp .env.example .env

# 4. Create the PostgreSQL database named in .env, then:
python manage.py migrate

# 5. Build CSS, seed roles, create an admin (optionally sample data)
npm run build
python manage.py setup_roles
python manage.py createsuperuser
python manage.py seed             # optional: realistic sample data
```

### Running it (day to day)

Two terminals:

```bash
npm run watch                     # terminal 1 — rebuilds CSS on template/component changes
```
```bash
python manage.py runserver        # terminal 2 — the Django dev server
```

Then open:

- **http://127.0.0.1:8000/styleguide/** — the UI component gallery
- **http://127.0.0.1:8000/admin/** — Django admin

> **Notes**
> - Styles won't render until `output.css` exists — run `npm run build` once, or
>   keep `npm run watch` running. It's generated (gitignored).
> - Hard-refresh (Ctrl+Shift+R) after CSS/JS changes; the browser caches `output.css`.
> - Icons are served from `/icons/`, which reads `node_modules/@iconify/json` — so
>   `npm install` must have run.

---

## Tech stack

Django 5 · PostgreSQL · django-cotton + Tailwind v4 + HTMX + Alpine · Iconify ·
Ruff · pytest. Full list and the purpose of each tool:
[`docs/engineering/tech-stack.md`](docs/engineering/tech-stack.md).

---

## Project status

Foundation complete: data layer, audit trail, GePG billing integration,
permissions, and a front-end component library (see `/styleguide/`). Feature
pages (login, dashboards, workflow screens) are next. See the docs above.
