# Project Structure

> The complete annotated layout. Every folder and file is explained **once**.
> For the *rules* behind these choices, see [`conventions.md`](conventions.md).
>
> Lineage: the two-tier `config/` + `apps/` layout (cookiecutter-django /
> HackSoft Django Styleguide). Adapt to fit — items marked **(optional)** are
> added only when the project actually needs them.

---

## Top level

```
project/
├── config/                 # Django project package — framework wiring only
├── apps/                   # all business apps, one folder each
├── templates/              # project-wide templates (base.html, errors, email)
├── static/                 # source static assets (css, js, img)
├── media/                  # user-uploaded files (gitignored)          (runtime)
├── locale/                 # translation catalogs                     (optional)
├── requirements/           # pinned dependencies, split by environment
├── docs/                   # architecture notes, ADRs, guides         (optional)
├── scripts/                # deploy / ops shell scripts               (optional)
├── .github/workflows/      # CI pipelines                             (optional)
├── manage.py               # Django CLI entrypoint
├── pyproject.toml          # Ruff + tool config, optionally deps + build
├── conftest.py             # pytest root fixtures / config
├── .pre-commit-config.yaml # git pre-commit hooks (Ruff, checks)      (optional)
├── Dockerfile              # container build                          (optional)
├── docker-compose.yml      # local service orchestration              (optional)
├── Makefile                # or justfile — shortcuts for common tasks (optional)
├── .env.example            # documents required env vars (no secrets)
├── .gitignore
├── LICENSE
├── CHANGELOG.md                                                       (optional)
├── CONTRIBUTING.md                                                    (optional)
└── README.md               # what it is, setup, run, test
```

| Entry | Purpose |
| --- | --- |
| `config/` | The Django *project* package. Holds settings, root URLconf, and server entrypoints — **no business logic**. Named `config` so it never collides with the product name. |
| `apps/` | Container for every business app. Keeps the repo root clean and makes app boundaries explicit. |
| `templates/` | Project-wide templates: the base layout, error pages (`404.html`, `500.html`), shared email templates. App-specific templates live inside each app. |
| `static/` | **Source** static assets you author. Distinct from the collected output — see `staticfiles/` below. |
| `media/` | User uploads at runtime. Gitignored; never committed. |
| `locale/` | `gettext` translation catalogs. Only when the project is internationalised. |
| `requirements/` | Dependency files split by environment (see below). Omit if using `pyproject.toml` + a lockfile instead. |
| `docs/` | Longer-form docs and Architecture Decision Records (ADRs). |
| `scripts/` | Operational shell scripts (deploy, backup) that aren't Django management commands. |
| `.github/workflows/` | CI: run tests + linters on push. |
| `manage.py` | Django's command-line utility. Untouched from `startproject`. |
| `pyproject.toml` | Central Python tool config (Ruff, pytest, mypy). May also declare dependencies + build metadata. |
| `conftest.py` | Root-level pytest fixtures and configuration shared across all test modules. |
| `.pre-commit-config.yaml` | Runs Ruff and hygiene checks before each commit, so bad code never lands. |
| `Dockerfile` / `docker-compose.yml` | Container build and local orchestration (db, cache, worker). |
| `Makefile` / `justfile` | One-word aliases for common commands (`make test`, `make run`). |
| `.env.example` | Template listing every required environment variable with dummy values. The real `.env` is gitignored. |
| `staticfiles/` | **(runtime, gitignored)** Output of `collectstatic` — the collected, production-served assets. Never edited by hand; not in the tree above because it's generated. |

---

## `config/` — the project package

```
config/
├── __init__.py
├── settings/
│   ├── __init__.py
│   ├── base.py             # shared defaults
│   ├── development.py      # local overrides (DEBUG=True, toolbar)
│   ├── production.py       # hardened prod settings
│   └── test.py             # fast settings for the test suite
├── urls.py                 # root URLconf — includes each app's urls
├── asgi.py                 # ASGI entrypoint (async servers, websockets)
├── wsgi.py                 # WSGI entrypoint (gunicorn/uwsgi)
└── celery.py               # Celery app instance                     (optional)
```

| Entry | Purpose |
| --- | --- |
| `settings/` | Settings split by environment instead of one file. `base.py` holds everything shared; each environment imports it and overrides. Selected via `DJANGO_SETTINGS_MODULE`. |
| `settings/base.py` | Common configuration — apps, middleware, templates, defaults. Never environment-specific secrets. |
| `settings/development.py` | Local dev: `DEBUG=True`, debug toolbar, console email backend. |
| `settings/production.py` | Security hardening: SSL redirect, secure cookies, HSTS, real hosts. |
| `settings/test.py` | Test speed: fast password hasher, local-memory cache, disposable DB. |
| `urls.py` | The root URL map. Only `include()`s app URLconfs and mounts admin/static — no view logic. |
| `asgi.py` / `wsgi.py` | Server entrypoints. ASGI for async/websockets, WSGI for traditional sync servers. |
| `celery.py` | Instantiates and configures the Celery app; imported by `__init__.py`. Only if using Celery. |

---

## `apps/<app>/` — a single application

The predictable internal shape. **Not every file is always present** — add each
when the app needs it. Keeping the *same* names everywhere means any app is
navigable once you know one.

```
apps/<app>/
├── __init__.py
├── apps.py                 # AppConfig — app metadata + signal registration
├── models/                 # a package once one file exceeds ~300 lines
│   ├── __init__.py         # re-exports so `from app.models import X` still works
│   └── <domain>.py         # models grouped by sub-domain
├── migrations/             # schema history (committed source code)
├── managers.py             # custom Manager / QuerySet classes         (optional)
├── services.py             # WRITE-side business logic
├── selectors.py            # READ-side query logic                     (optional)
├── enums.py                # TextChoices / IntegerChoices classes      (optional)
├── constants.py            # module-level constants, magic values      (optional)
├── exceptions.py           # domain-specific exception classes         (optional)
├── forms.py                # Django forms / ModelForms
├── admin.py                # Django admin registration
├── signals.py              # signal handlers (wired in apps.py)        (optional)
├── permissions.py          # authorization checks                     (optional)
├── filters.py              # django-filter FilterSets                  (optional)
├── tasks.py                # Celery/async tasks                        (optional)
├── urls.py                 # app URLconf (app_name namespace)
├── views.py                # thin views — parse, call service, respond
├── templates/<app>/        # app-namespaced templates
├── static/<app>/           # app-specific static assets                (optional)
├── api/                    # DRF layer                                 (optional)
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
└── tests/
    ├── __init__.py
    ├── factories.py        # factory_boy factories (also used for seeding)
    ├── test_services.py
    ├── test_selectors.py
    └── test_views.py
```

| Entry | Purpose |
| --- | --- |
| `apps.py` | The `AppConfig`. Sets the app label and, in `ready()`, registers signals. Required by Django. |
| `models/` | Data models. A *package* (folder) once a single file grows past ~300 lines; `__init__.py` re-exports each model so import paths stay stable. |
| `migrations/` | Auto-generated schema changes. Committed — they are the schema's version history. |
| `managers.py` | Custom `Manager`/`QuerySet` methods holding reusable table-level queries (e.g. `Invoice.objects.unpaid()`). |
| `services.py` | The **write** side of business logic: validates rules, coordinates models, wraps writes in transactions, calls external gateways. Views call these. |
| `selectors.py` | The **read** side: complex queries, annotations, joins — so views and templates stay dumb. |
| `enums.py` | `TextChoices` / `IntegerChoices` enum classes used by model fields and logic. |
| `constants.py` | Fixed values and magic numbers/strings, named once in a central place. |
| `exceptions.py` | Domain-specific exceptions services raise so callers can react precisely (instead of bare `except`). |
| `forms.py` | Form and ModelForm classes — input validation for server-rendered views. |
| `admin.py` | `ModelAdmin` registrations and customisation for the Django admin. |
| `signals.py` | Signal receivers (`post_save`, etc.), connected in `apps.py:ready()`. Use sparingly. |
| `permissions.py` | Authorization logic — who may do what — kept out of views. |
| `filters.py` | `django-filter` FilterSets for list filtering/search. |
| `tasks.py` | Background/async tasks (Celery). Take IDs, not model instances; idempotent. |
| `urls.py` | The app's URL patterns under an `app_name` namespace. Included by `config/urls.py`. |
| `views.py` | Thin request handlers: parse input, call a service/selector, return a response. No business rules. |
| `templates/<app>/` | Templates namespaced by app folder to avoid cross-app name collisions. |
| `static/<app>/` | Static assets belonging only to this app, namespaced the same way. |
| `api/` | The DRF layer, isolated from server-rendered views: `serializers.py` (validate/shape), `views.py` (viewsets), `urls.py` (routers). |
| `tests/` | Test package. `factories.py` holds `factory_boy` factories reused for both tests and seeding; test modules mirror the code files they cover. |

---

## `requirements/` — dependencies

```
requirements/
├── base.txt                # runtime deps needed everywhere
├── development.txt          # base + dev tools (ruff, pytest, debug toolbar)
└── production.txt           # base + prod-only (gunicorn, sentry)
```

| File | Purpose |
| --- | --- |
| `base.txt` | Packages the app needs to run in any environment. |
| `development.txt` | Imports `base.txt` (`-r base.txt`) and adds linters, test tools, local helpers. |
| `production.txt` | Imports `base.txt` and adds production-only servers/monitoring. |

> Alternative: declare dependencies in `pyproject.toml` with a lockfile
> (uv / poetry) and drop this folder. Pick one approach, not both.

---

## What deliberately does **not** exist

- **No loose scripts at the repo root** (`fix.py`, `setup_x.py`). Operational
  one-offs are management commands (`apps/<app>/management/commands/`); ops
  shells go in `scripts/`.
- **No committed database dumps** (`*.sql`, full-DB `*.json`). Seed data comes
  from factories via a management command.
- **No committed virtualenv, `.env`, or `staticfiles/`** — all gitignored.
- **No business logic in `config/`, `views`, `serializers`, or templates** — it
  lives in `services.py` / `selectors.py`.
