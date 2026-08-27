# Django & Python Conventions

> A portable, opinionated standard for building maintainable Django projects.
> Drop it into any repository as the team's shared rulebook.
>
> Style rules marked **(Ruff)** are enforced mechanically by Ruff via
> `pyproject.toml`. The rest are enforced in code review.
>
> **Convention over configuration:** when Django or Python offers an idiomatic
> way, use it. Deviate only with a documented reason.

---

## Table of contents

1. [Project layout](#1-project-layout)
2. [Application architecture](#2-application-architecture)
3. [Settings & configuration](#3-settings--configuration)
4. [Naming](#4-naming)
5. [Models](#5-models)
6. [Migrations](#6-migrations)
7. [QuerySets & the ORM](#7-querysets--the-orm)
8. [Views & business logic](#8-views--business-logic)
9. [URLs](#9-urls)
10. [Forms & validation](#10-forms--validation)
11. [Templates & front-end](#11-templates--front-end)
12. [APIs (Django REST Framework)](#12-apis-django-rest-framework)
13. [Error handling & logging](#13-error-handling--logging)
14. [Security](#14-security)
15. [Authentication & users](#15-authentication--users)
16. [Async, tasks & caching](#16-async-tasks--caching)
17. [Testing](#17-testing)
18. [Data seeding & fixtures](#18-data-seeding--fixtures)
19. [Management commands](#19-management-commands)
20. [Python style & tooling](#20-python-style--tooling)
21. [Dependencies & environments](#21-dependencies--environments)
22. [Git & repository hygiene](#22-git--repository-hygiene)
23. [Documentation](#23-documentation)
24. [Pre-commit checklist](#pre-commit-checklist)

---

## 1. Project layout

> **Full annotated tree lives in [`project-structure.md`](project-structure.md).**
> This section states the principles; that file explains every folder and file.

### There is no single official layout

Django's `startapp` produces a *flat* layout (apps at the repo root) — official,
but it does not scale for larger projects. The convention below is the **two-tier
`apps/` + `config/` layout** popularised by cookiecutter-django and the HackSoft
Django Styleguide. It is a widely-adopted community standard, **not** a mandate —
adapt it to the project.

```
project/
├── config/       # the Django project package (settings, root urls, wsgi/asgi)
├── apps/         # ALL business apps live here, one folder per app
├── templates/    # project-wide templates
├── static/       # source static assets
├── requirements/ # or pyproject.toml + lockfile
├── manage.py
└── pyproject.toml
```

### Load-bearing principles

- **`config/` + `apps/` split.** The project package holds framework wiring
  only; every business app lives under `apps/`. Never a flat pile at the root.
- **Name the project package `config`** (not the product name) — it ages better
  and avoids the `myproduct/myproduct/` confusion.
- **One responsibility per app.** If you can't describe it in one sentence,
  split it.
- **Each app is internally consistent** — same predictable set of files
  (`services.py`, `selectors.py`, `apps.py`, …) so any app is navigable once you
  know one. Full list and rationale in
  [`project-structure.md`](project-structure.md).

### Include only when the project uses them

Celery (`config/celery.py`, per-app `tasks.py`), DRF (per-app `api/`), i18n
(`locale/`), Docker, and CI (`.github/`) are **optional** — add them when the
need is real, not by default. See [`project-structure.md`](project-structure.md)
for where each belongs.

---

## 2. Application architecture

### Layered dependencies — the core rule

**Imports point downward only. Never sideways, never up.**

```
L4  ENTRYPOINTS   dashboards, landing pages          (thin)
      │ imports ↓ only
L3  DOMAIN APPS   the real business logic
      │ imports ↓ only
L2  ACCOUNTS      users, roles, permissions
      │ imports ↓ only
L1  CORE / SHARED base models, reference data, utils
```

- A lower layer never imports a higher one.
- Two apps in the same layer must not import each other's models. Shared data
  belongs one layer down (in `core`).
- This keeps each app independently understandable and prevents circular
  imports.

### The service layer

Business logic lives in **`services.py`** (write operations) and optionally
**`selectors.py`** (read queries), *not* in views, models, or serializers.

```
request → view (thin) → service (business rules) → model/manager → response
```

- **Services** orchestrate: validate business rules, coordinate multiple
  models, wrap writes in transactions, call external gateways.
- **Selectors** encapsulate complex reads (annotations, joins, filtering) so
  views and templates stay dumb.
- **Models** hold row-level logic and invariants; **managers/querysets** hold
  reusable table-level queries.

This separation is what keeps views ~15 lines and makes logic testable without
HTTP.

---

## 3. Settings & configuration

- **Split settings** into `config/settings/{base,development,production,test}.py`.
  `base.py` holds shared defaults; environment files import from it and override.
- **Select via `DJANGO_SETTINGS_MODULE`**, defaulting to development locally.
- **Twelve-factor config:** every secret and environment-specific value comes
  from an environment variable (`python-decouple`, `django-environ`, or
  `os.environ`). Nothing sensitive is committed.
- **`.env.example`** lists every required variable with safe dummy values.
- **`DEBUG` defaults to `False`.** Only `development.py` sets it `True`. A
  missing env var must never silently enable debug mode in production.
- **`SECRET_KEY` has no default** — the app should refuse to start without it.
- **Fail loud on misconfiguration.** Never wrap `DATABASES` or other config in a
  `try/except` that masks a missing or mistyped value.
- **`USE_TZ = True`.** Store timezone-aware datetimes even for single-timezone
  apps; set `TIME_ZONE` for display.
- **Keep third-party integration config** (payment gateways, SMS, etc.) in its
  own config module or a DB-backed settings model — not scattered through
  `base.py`.
- **Remove deprecated settings** (`USE_L10N`, etc.) when upgrading Django.

---

## 4. Naming

| Thing            | Convention                                 | Example                 |
| ---------------- | ------------------------------------------ | ----------------------- |
| Model class      | `PascalCase`, **singular**, no type suffix | `Order`, `Invoice`      |
| Model field      | `snake_case`                               | `created_at`            |
| Boolean field    | prefix `is_` / `has_` / `can_`             | `is_active`             |
| Function / var   | `snake_case`                               | `create_invoice`        |
| Constant         | `UPPER_SNAKE_CASE`                         | `DEFAULT_CURRENCY`      |
| Class            | `PascalCase`                               | `InvoiceService`        |
| App package      | lowercase, plural, no `_app` suffix        | `orders`, `billing`     |
| URL name         | `snake_case`, app-namespaced               | `billing:invoice_detail`|
| Template         | `snake_case.html`                          | `invoice_detail.html`   |
| Test file        | `test_*.py`                                | `test_services.py`      |

- **No redundant type suffixes** (`OrderTB`, `orders_app`). A model is a table;
  an app is an app.
- **Reverse relations read as plurals** via `related_name` (see Models).
- **Be consistent, not clever** — predictable names beat short ones.

---

## 5. Models

- **Money is `DecimalField`** (`max_digits`, `decimal_places`). Never
  `FloatField` — floats can't represent currency exactly and drift on
  aggregation.
- **`related_name` on every `ForeignKey` / `ManyToManyField`.** Reverse lookups
  should read naturally: `order.invoices.all()`.
- **Set `on_delete` deliberately** — `CASCADE`, `PROTECT`, `SET_NULL`. Never
  pick it by habit; it's a data-integrity decision.
- **`choices` as `TextChoices` / `IntegerChoices` enum classes**, not loose
  tuples:
  ```python
  class Status(models.TextChoices):
      PENDING = "PENDING", "Pending"
      PAID    = "PAID", "Paid"
  ```
- **Text fields use `blank=True` (+ `default=""` where appropriate), not
  `null=True`.** Reserve `null=True` for non-string columns; `null` on a
  `CharField` creates two "empty" values (`""` and `None`).
- **`__str__` on every model.**
- **`class Meta`:** set `ordering`, `verbose_name`, `constraints`, and
  `indexes` where relevant. Prefer `Meta.constraints`
  (`UniqueConstraint`, `CheckConstraint`) over field-level `unique=True` for
  anything composite or conditional.
- **Timestamps:** `created_at = DateTimeField(auto_now_add=True)`,
  `updated_at = DateTimeField(auto_now=True)`. Consider an abstract
  `TimeStampedModel` base in `core`.
- **Row-level logic → model methods and `@property`.**
  **Table-level queries → custom `Manager` / `QuerySet` methods.** This is the
  only place "fat" belongs — never fat views.
- **Split `models.py` into a package** once it passes ~300 lines.
- **Add DB indexes** for fields you filter or order by frequently.
- **Validate in `clean()`** for cross-field model invariants; call
  `full_clean()` in services before saving when not going through a form.

---

## 6. Migrations

- **Commit migrations** — they are source code and part of the schema history.
- **One logical change per migration**; give data migrations descriptive names.
- **Review generated SQL** for expensive operations (`sqlmigrate`).
- **Data migrations use `RunPython`** with a reverse function; never import
  models directly — use `apps.get_model()` inside the migration.
- **Never edit an applied migration.** Add a new one.
- **Squash** long migration chains periodically (`squashmigrations`).
- **Zero-downtime discipline** for production: add columns nullable/with
  defaults first, backfill, then tighten — don't combine schema and data
  changes that lock tables.

---

## 7. QuerySets & the ORM

- **Kill N+1 queries:** `select_related` for FK/one-to-one,
  `prefetch_related` for M2M and reverse FK. Profile with
  `django-debug-toolbar` or `assertNumQueries`.
- **`get_object_or_404`** instead of manual `try/except DoesNotExist` in views.
- **`.exists()`** for existence checks, **`.count()`** for counts — never
  `len(qs)` or `bool(qs)` when you don't need the rows.
- **`.only()` / `.defer()`** to trim columns on hot paths; **`.values()` /
  `.values_list()`** when you need dicts/tuples, not model instances.
- **Aggregate in the database** (`annotate`, `aggregate`, `F`, `Q`,
  conditional `Case/When`) rather than in Python loops.
- **`bulk_create` / `bulk_update`** for batch writes.
- **`update()` / `F()` expressions** for atomic field updates instead of
  read-modify-write races.
- **Push query logic into managers/selectors** — views should not compose long
  filter chains inline.
- **Raw SQL only as a last resort**, always parameterized (never string
  interpolation), isolated behind a selector.

---

## 8. Views & business logic

- **Thin views.** Parse the request → call one service/selector → return a
  response. Target ~15 lines.
- **No business rules in views.** They belong in the service layer.
- **Wrap multi-table writes in `@transaction.atomic`** (or
  `with transaction.atomic():`). A partial write is worse than a failed one.
- **Choose one view style per concern and apply it consistently** — CBVs
  (`ListView`, `DetailView`, generic editing views) for standard CRUD, FBVs for
  bespoke logic. Don't mix arbitrarily within an app.
- **Enforce auth at the boundary:** `LoginRequiredMixin` /
  `PermissionRequiredMixin` on CBVs, `@login_required` /
  `@permission_required` on FBVs.
- **Return the right status codes**; use `redirect()` after successful POST
  (Post/Redirect/Get) to avoid double submission.
- **Use the `messages` framework** for user feedback.
- **Paginate** any unbounded list.

---

## 9. URLs

- **Use `path()`** with typed converters (`<int:pk>`, `<slug:slug>`); reserve
  `re_path()` for genuine regex needs.
- **Namespace every app** (`app_name = "billing"`) and reference names via the
  namespace (`{% url 'billing:invoice_detail' %}`, `reverse('billing:...')`).
- **Never hard-code URLs** in templates, views, or redirects — always
  `reverse` / `{% url %}` / `get_absolute_url()`.
- **No wildcard imports** in URLconfs; import views explicitly.
- **Keep URL prefixes consistent** and human-readable across apps.
- **Include app URLs** from the project URLconf; don't define app routes at the
  project level.

---

## 10. Forms & validation

- **Validate user input with Forms / ModelForms**, not by hand in views.
- **`clean_<field>()`** for single-field rules, **`clean()`** for cross-field
  rules; raise `ValidationError`.
- **Keep forms about input validation**; put persistence and side effects in the
  service the form's view calls.
- **Use `ModelForm.Meta.fields` explicitly** — never `fields = "__all__"` on
  anything user-facing (it silently exposes new fields later).

---

## 11. Templates & front-end

- **Namespace template directories:** `app/templates/app/name.html` to avoid
  cross-app collisions.
- **Base template + `{% block %}` inheritance**; no copy-pasted page chrome.
- **Logic-free templates.** No querysets, business rules, or heavy computation
  in templates — prepare data in the view/selector. Custom template tags/filters
  for genuinely reusable presentation only.
- **Always `{% csrf_token %}`** in POST forms.
- **Autoescaping stays on;** use `|safe` / `mark_safe` only on trusted content.
- **Load static via `{% static %}`**, never hard-coded paths; run
  `collectstatic` for production and serve via WhiteNoise/CDN.
- **Progressive enhancement** (htmx/Alpine/vanilla) over heavy SPA frameworks
  unless the product genuinely needs one.

---

## 12. APIs (Django REST Framework)

- **Use DRF for JSON APIs and webhooks** — not hand-rolled `JsonResponse`
  views.
- **Serializers validate and shape data**; business logic still lives in
  services, called from the view/viewset.
- **ViewSets + routers** for standard CRUD; `APIView` for bespoke endpoints.
- **Version the API** (`/api/v1/`).
- **Explicit permission classes** on every view; never rely on defaults.
- **Paginate list endpoints** and set sane throttles.
- **Document with OpenAPI** (`drf-spectacular`).

---

## 13. Error handling & logging

- **Never write a bare `except:`.** Catch specific exception types. A bare
  except swallows `KeyboardInterrupt`, `SystemExit`, and real bugs — and is
  especially dangerous around payments, crypto, and external I/O.
- **Don't silence exceptions** you can't handle — let them propagate or
  re-raise with context (`raise ... from err`).
- **Log with the `logging` module**, never `print()`. One logger per module:
  `logger = logging.getLogger(__name__)`.
- **Log levels mean things:** `DEBUG` (dev detail), `INFO` (normal events),
  `WARNING` (recoverable oddity), `ERROR` (failed operation), `CRITICAL`
  (system-level). Don't log at `ERROR` for expected control flow.
- **Never log secrets or PII.**
- **Configure structured logging + an error tracker** (e.g. Sentry) in
  production.
- **Raise domain-specific exceptions** from services so callers can react
  precisely.

---

## 14. Security

- **Keep `SECRET_KEY`, DB credentials, and API keys in env vars**, never in
  source or settings defaults.
- **Production settings:** `DEBUG = False`, correct `ALLOWED_HOSTS`,
  `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`,
  `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`,
  `X_FRAME_OPTIONS = "DENY"`. Verify with `manage.py check --deploy`.
- **Never disable CSRF** to "make it work"; for APIs use token/session auth
  properly.
- **Trust the ORM and Forms** — they parameterize queries and escape output.
  Any raw SQL must be parameterized.
- **Enforce authorization on every view** — authentication is not
  authorization; check object-level permissions.
- **Rate-limit / lock out** brute-force login attempts (e.g. django-axes).
- **Validate and sanitize file uploads** (type, size, storage location);
  never trust `content_type`.
- **Keep dependencies patched;** scan with `pip-audit` / Dependabot.

---

## 15. Authentication & users

- **Define a custom user model on day one** (`AUTH_USER_MODEL`), even if it just
  extends `AbstractUser`. Swapping it later is extremely painful.
- **Reference the user via `get_user_model()` / `settings.AUTH_USER_MODEL`**,
  never `django.contrib.auth.models.User` directly.
- **Roles/permissions via Django groups & permissions** or a dedicated
  authorization layer — not ad hoc boolean flags scattered across models.
- **Hash passwords with Django's framework** (never store or log raw
  passwords); use its password validators.

---

## 16. Async, tasks & caching

- **Offload slow / external work** (email, SMS, PDF generation, third-party API
  calls) to a task queue (Celery, Django-Q, RQ) — never block the request.
- **Tasks are idempotent** and take primitives (IDs), not ORM instances, as
  arguments.
- **Cache deliberately** (`cache` framework, per-view, or template fragment)
  and set explicit TTLs; have an invalidation strategy.
- **Use `select_for_update`** inside transactions to guard against race
  conditions on concurrent writes.

---

## 17. Testing

- **`pytest` + `pytest-django`** as the runner. Tests live in
  `apps/<app>/tests/` as `test_*.py`.
- **Test the service layer first** — that's where the business rules are, and
  it's testable without HTTP.
- **`factory_boy`** for test data (doubles as seeding — see §18).
- **`assertNumQueries` / query-count assertions** to catch N+1 regressions.
- **Test behavior, not implementation;** avoid over-mocking your own code.
- **Fast, isolated, deterministic** — no network, no reliance on test order, no
  shared mutable state.
- **A separate `test.py` settings** module (fast password hasher, local-memory
  cache, in-memory or disposable DB).
- **CI runs the full suite + linters** on every push; keep the build green.

---

## 18. Data seeding & fixtures

- **Seed via a management command backed by `factory_boy`** (or model
  `bulk_create`) — never commit full SQL/JSON database dumps.
- **Reuse test factories for seeding** — one solution, two problems solved.
- **Small, curated fixtures only** (`loaddata`) for genuinely static reference
  data; keep them versioned and minimal.
- **Never commit real customer/production data** to the repo.

---

## 19. Management commands

- **Every one-off / operational script is a management command**
  (`apps/<app>/management/commands/<name>.py`), runnable via `manage.py`,
  versioned and discoverable via `manage.py help`.
- **Nothing loose at the repo root.** No `fix_*.py`, `setup_*.py`, ad hoc
  scripts.
- **Commands are idempotent** where possible, use `self.stdout` /
  `self.stderr`, expose options via `add_arguments`, and wrap writes in
  transactions.

---

## 20. Python style & tooling

- **Ruff** is the single linter + formatter + import sorter, configured in
  `pyproject.toml`. Run it (and ideally `pre-commit`) before every commit.
  **(Ruff)**
- **PEP 8 line length, spacing, and naming.** **(Ruff)**
- **No wildcard imports** (`from x import *`) — they break tooling and hide
  symbol origins. **(Ruff)**
- **Import order:** standard library → third-party → Django → local. **(Ruff)**
- **`pathlib` over `os.path`.**
- **Type hints** at least on service-layer and public function boundaries;
  consider `mypy` / `pyright` in CI.
- **f-strings** for formatting; no `%` or `.format()` for new code.
- **Docstrings** on modules, public functions, and classes (see §23).
- **No dead code, commented-out blocks, or fix-log comments** (`# FIXED:`,
  `# NEW:`) — that's what version control is for.

---

## 21. Dependencies & environments

- **Isolate with a virtualenv** (`venv`, or a tool like `uv`/`poetry`). Never
  commit the environment directory.
- **Pin dependencies** — `requirements/{base,development,production}.txt` with a
  lockfile, or `pyproject.toml` + lockfile (uv/poetry).
- **Separate dev-only deps** (linters, test tools) from runtime deps.
- **Keep dependencies current and audited** (`pip-audit`, Dependabot).
- **`.python-version` / documented interpreter version** so environments match.

---

## 22. Git & repository hygiene

- **`.gitignore` must cover:** `venv/`/`.venv/`, `*.sqlite3`, `.env`,
  `__pycache__/`, `*.pyc`, `/media/`, `/staticfiles/`, IDE folders, and DB
  dumps (`*.sql`, non-fixture `*.json`).
- **Never commit secrets, `.env` files, credentials, or certificates.** If one
  leaks, rotate it and scrub history.
- **Small, focused commits** with imperative messages ("Add invoice service",
  not "fixes").
- **Branch per change; PR + review before merge.** CI must pass.
- **Migrations are committed with the model change that produced them.**

---

## 23. Documentation

- **`README.md`:** what the project is, how to set it up, run it, and test it.
- **`.env.example`** documents required configuration.
- **Docstrings** describe purpose, parameters, return values, side effects, and
  raised exceptions — follow the ecosystem's convention (Google/NumPy/reST).
- **Comment the *why*, not the *what*.** Explain non-obvious decisions,
  business rules, trade-offs, and constraints — not what readable code already
  says.
- **Keep an architecture note / ADRs** for significant decisions so future
  maintainers understand the reasoning.

---

## Pre-commit checklist

- [ ] No sideways/upward imports across app layers
- [ ] Business logic in `services.py`; views stay thin
- [ ] Money fields are `DecimalField`
- [ ] `related_name` and deliberate `on_delete` on new relations
- [ ] Multi-table writes wrapped in a transaction
- [ ] No N+1 queries (`select_related` / `prefetch_related`)
- [ ] No bare `except:`; logging instead of `print()`
- [ ] User input validated via Forms/serializers
- [ ] URLs namespaced and reversed, never hard-coded
- [ ] No secrets, env files, or DB dumps staged
- [ ] Tests added/updated for changed behavior
- [ ] Ruff passes clean
```
