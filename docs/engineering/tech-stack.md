# Tech Stack

The tools in use and why each is here. Two guiding principles shape the choices:

- **Convention over configuration** — prefer the idiomatic Django/Tailwind way.
- **Self-hosted, no CDN** — every front-end asset is served from our own origin
  (CSP-safe, privacy-safe, no third-party dependency at runtime).

---

## Backend

| Tool | Purpose |
| --- | --- |
| **Python 3.13** | Language runtime. |
| **Django 5** | Web framework — ORM, migrations, admin, auth, templating. |
| **PostgreSQL** | Primary database. |
| **psycopg 3** | PostgreSQL driver for Django. |
| **python-decouple** | Reads configuration/secrets from environment (`.env`), keeping them out of code. |

## Data integrity & audit

| Tool | Purpose |
| --- | --- |
| **django-auditlog** | Records a full change history (create/update/delete, actor, field diffs) in one central `LogEntry` table. |
| *soft delete + audit columns* | Our own `core.BaseModel` — nothing is hard-deleted; every row carries created/updated/deleted actor + timestamps. |

## Payments (GePG)

| Tool | Purpose |
| --- | --- |
| **requests** | HTTP client for the GePG bill-submission API. |
| **cryptography** | PKCS#12 SHA256-RSA digital signing/verification of GePG XML. |

## Front-end

Server-rendered Django templates, progressively enhanced. No SPA, no build-time
framework — just components, utility CSS, and small JS libraries.

| Tool | Purpose |
| --- | --- |
| **django-cotton** | HTML component system (`<c-atoms.ui.button>`) — reusable, composable templates organised by Atomic Design. |
| **Tailwind CSS v4** | Utility-first styling, built via npm to a single vendored `output.css`. |
| **HTMX** | Server-driven interactivity — swap HTML fragments from the server (lists, forms, partial updates) without writing JS. |
| **Alpine.js** | Client-only interactivity — dropdowns, modals, toggles, transitions — the things HTMX shouldn't round-trip to the server for. |
| **Tom Select** | Turns `<select>` value pickers into searchable comboboxes (filter, keyboard nav, multi-select). |
| **django-iconify** + **iconify-icon** | Icons: a self-hosted Iconify API (`/icons/`) backed by `@iconify/json`, rendered by the `iconify-icon` web component. Any of ~200k icons (Lucide, Heroicons, Tabler…) by name. |
| **Inter** (`@fontsource-variable/inter`) | Self-hosted variable UI font (one woff2, all weights, `font-display: swap`). |

**HTMX vs Alpine** — complementary, not overlapping: HTMX = *server* interactions
(data), Alpine = *client* state (UI). Both auto-initialise on HTMX-swapped
content via `static/js/app.js`.

## Developer tooling

| Tool | Purpose |
| --- | --- |
| **Ruff** | Linter + formatter + import sorter (one tool), configured in `pyproject.toml`. |
| **pytest** + **pytest-django** | Test runner; tests live in `apps/<app>/tests/`. |
| **factory_boy** | Test-data factories — also power the `seed` command (one source for tests and dev data). |
| **pre-commit** | Runs Ruff + hygiene checks before each commit. |
| **mypy** | Optional static type checking (service-layer boundaries). |
| **django-debug-toolbar** | Request/query inspection in development. |
| **Node / npm** | Front-end build toolchain (Tailwind, vendored JS/font packages). |

## Where things run

- **Python packages** → `requirements/` (base/development), installed into `.venv`.
- **npm packages** → `package.json`; only build outputs/vendored files are served.
  `output.css` is generated (gitignored); `node_modules/` is gitignored; vendored
  JS and the font woff2 are committed under `static/`.
- **Build step** — `npm run build` produces `static/css/output.css`; run it before
  `collectstatic` in CI/deploy.
