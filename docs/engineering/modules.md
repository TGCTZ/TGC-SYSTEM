# Module Catalog

> The definitive list of TGC-SYSTEM's modules (Django apps), their names,
> responsibilities, and dependency layer. **Names are the team's shared
> vocabulary** — use these exact names in code, conversation, and tickets.
>
> Layering rule (imports point downward only) is defined in
> [`conventions.md` §2](conventions.md). Legacy mapping is in
> [`legacy-mifumo-modules.md`](../domain/legacy-mifumo-modules.md).

---

## 1. The modules

| Layer | Module | One-line responsibility |
| --- | --- | --- |
| **L1** | `core` | Shared base models, reference/master data, cross-cutting utilities. |
| **L2** | `accounts` | Users, roles, permissions, authentication. |
| **L3** | `orders` | Customers, orders, and the stones logged against them (intake). |
| **L3** | `identification` | Gemmological examination — identification reports and findings. |
| **L3** | `production` | Workshop processing (sonara / carving / lapidary) and quality assurance. |
| **L3** | `billing` | Bills, line items, payments, GePG integration, reconciliation. |
| **L3** | `certificates` | Certificate issuance, QR codes, public verification. |
| **L4** | `reports` | Management reports and exports (reads across domain modules). |
| **L4** | `dashboard` | Landing pages and navigation shells (thin entrypoints). |

**9 modules** — down from MIFUMO's 19 (12 active + 7 empty).

---

## 2. Dependency layers

```
L4   reports · dashboard          (read/aggregate; import ↓ only)
        │
L3   orders · identification · production · billing · certificates
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
**Owns:** the abstract `TimeStampedModel` base; the `StoneStatus` enum (fixed
workflow stages, code-defined); reference lookups — `StoneType`, `Species`,
`Variety`, `Color`, `Transparency`, `Origin`, `Treatment`, `ShapeCut`,
`OpticCharacter`, `SiUnit`, `Instrument`; and `StonePrice` (price list).
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

### `production` (L3)
**Owns:** the single `Production` model with a `type` field
(sonara / carving / lapidary), assignment, and QA results.
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
| `production` | function name | 3 workshop apps | One module, one `type` field — replaces sonara/carving/lapidary. |
| `certificates` | plural entity | (buried in gemmology) | Promoted to its own module; owns QR + verification. |
| `core` / `accounts` | conventional | — | Standard Django community names. |

---

## 5. Build order

Build **bottom-up** so each module's dependencies already exist:

```
1. core          ← no dependencies; build first
2. accounts      ← already scaffolded (custom User)
3. orders        ← the spine (Customer → Order → Stone)
4. identification / production / billing   ← attach to orders
5. certificates  ← needs identification
6. reports / dashboard   ← read across everything; build last
```

> Current status: `core` and `accounts` are scaffolded. The rest are created as
> we reach them — no empty app is scaffolded ahead of need
> ([`project-structure.md`](project-structure.md), "What deliberately does not
> exist").
