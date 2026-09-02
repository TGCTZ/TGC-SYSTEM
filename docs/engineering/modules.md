# Module Catalog

> The definitive list of TGC-SYSTEM's modules (Django apps), their names,
> responsibilities, and dependency layer. **Names are the team's shared
> vocabulary** — use these exact names in code, conversation, and tickets.
>
> Layering rule (imports point downward only) is defined in
> [`conventions.md` §2](conventions.md).

---

## 1. The modules

| Layer | Module | One-line responsibility |
| --- | --- | --- |
| **L1** | `core` | Shared base models, reference/master data, cross-cutting utilities. |
| **L2** | `accounts` | Users, roles, permissions, authentication. |
| **L3** | `orders` | Customers, orders, and the stones logged against them (intake). |
| **L3** | `identification` | Gemmological examination — identification reports and findings. |
| **L3** | `billing` | Bills, line items, payments, GePG integration, reconciliation. |
| **L3** | `certificates` | Certificate issuance, QR codes, public verification. |
| **L4** | `reports` | Management reports and exports (reads across domain modules). |
| **L4** | `dashboard` | Landing pages and navigation shells (thin entrypoints). |
| **L4** | `adminpanel` | Generic model-admin, roles & permissions portal, and users management at `/manage/` + `/users/`. |

**9 focused modules**, each with a single clear responsibility.

---

## 2. Dependency layers

```
L4   reports · dashboard · adminpanel   (read/aggregate; import ↓ only)
        │
L3   orders · identification · billing · certificates
        │                         (the business; import ↓ only)
L2   accounts                     (import ↓ only)
        │
L1   core                         (depends on nothing above)
```

Same-layer modules must **not** import each other's models. Shared needs go down
to `core`. Cross-domain coordination happens through the service layer, not
through sideways model imports.

---

## 3. Module details

### `core` (L1)
**Owns:** the abstract `BaseModel` base (audit columns + soft delete); code-defined
**enums** — `StoneStatus`, `StoneCategory`, `WeightUnit`, `Transparency`,
`OpticCharacter`, `NatureType`, `Treatment`, `ColorGroup`; admin-managed
**reference lookups** — `StoneType`, `Species`, `Variety`, `Color`, `Origin`,
`ShapeCut`, `Instrument`; and `StonePrice` (the flat price list).
**Depends on:** nothing above it.

### `accounts` (L2)
**Owns:** the custom `User` model, roles, and permission logic.
**Depends on:** `core`.

### `orders` (L3)  *(the intake desk)*
**Owns:** `Customer`, `Order`, `Stone`, and `StatusHistory` (the audit trail of
stone status transitions).
**Depends on:** `core`, `accounts`.

### `identification` (L3)
**Owns:** `IdentificationReport` (one per stone) and its findings; references
`core` lookups for every attribute.
**Depends on:** `core`, `accounts`, `orders`.

### `billing` (L3)
**Owns:** `Bill` (one per order), `BillItem` (one per stone, price snapshotted),
`Payment`, `ServiceProvider`, reconciliation; GePG client code in a `gateways/`
subpackage.
**Depends on:** `core`, `accounts`, `orders`.

### `certificates` (L3)
**Owns:** `Certificate` (one per stone), QR generation, PDF rendering, public
verification, access logs.
**Depends on:** `core`, `accounts`, `orders`, `identification`.

### `reports` (L4)
**Owns:** report definitions, generation, and exports. Reads across domain
modules; holds little state of its own.
**Depends on:** domain modules (read-only).

### `dashboard` (L4)
**Owns:** landing pages, role-based navigation. No business logic.
**Depends on:** domain modules (read-only).

### `adminpanel` (L4)
**Owns:** the generic model-admin framework (a `ModelPanel` registry — apps register
models in their own `panels.py`, getting styled list/detail/CRUD screens at
`/manage/<app>/<model>/`), the **roles & permissions portal** (`/manage/roles/` — Group
CRUD with a live permission matrix), and an admin dashboard (KPI cards + audit-log
activity feed). The bespoke **users module** (`/users/`, `accounts.users_views`) is a
sibling. Only safe reference models are registered (see `core/panels.py`); workflow
models keep their service-driven flows. Django's `/admin/` remains available.
**Depends on:** `core`, `accounts` (read/registry only).

---

## 4. Naming decisions (why these names)

Names were chosen for **clarity in everyday communication**, following
[`conventions.md` §4](conventions.md) (lowercase, no `_app` suffix, no `TB`
model suffix).

| Module | Chosen | Over | Reason |
| --- | --- | --- | --- |
| `orders` | entity name | `reception`, `intake` | "the orders module" is unambiguous and maps to the `Order` model. |
| `identification` | function name | `gemmology`, `analysis` | Describes what the module *does*; `gemmology` was too broad. |
| `reports` | plural entity | `reporting` | Consistent with `orders`, `certificates`. |
| `certificates` | plural entity | (buried in gemmology) | Promoted to its own module; owns QR + verification. |
| `core` / `accounts` | conventional | — | Standard Django community names. |

---

## 5. Build order

Build **bottom-up** so each module's dependencies already exist:

```
1. core          ← no dependencies; build first
2. accounts      ← already scaffolded (custom User)
3. orders        ← the spine (Customer → Order → Stone)
4. identification / billing   ← attach to orders
5. certificates  ← needs identification
6. reports / dashboard   ← read across everything; build last
```

> Current status: `core` and `accounts` are scaffolded. The rest are created as
> we reach them — no empty app is scaffolded ahead of need
> ([`project-structure.md`](project-structure.md), "What deliberately does not
> exist").
