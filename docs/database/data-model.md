# Database Schema

> The complete data model for TGC-SYSTEM, by module. Column types follow
> [`conventions.md` §5](../engineering/conventions.md): money is `Decimal`, text
> uses `blank`/`default=""` (not `null`), choices are enums, every table has
> `created_at`/`updated_at`.
>
> **Rendered ERD:** the machine-readable version is [`schema.dbml`](schema.dbml)
> — paste it into [dbdiagram.io](https://dbdiagram.io) to view the diagram. This
> file is the human-readable companion; keep the two in sync.
>
> **(open: Bn / Cn)** marks a column or rule that depends on a question in
> [`domain-questions.md`](../domain/domain-questions.md) and may change.

---

## Normalization principles

The schema is normalized to third normal form, with a few deliberate,
documented exceptions:

- **Customer is a first-class entity.** `Order` and `Bill` reference a single
  `Customer` record rather than storing name/phone/company inline, so a
  returning customer is recorded once.
- **One identification report per stone.** All findings live on a single
  `IdentificationReport`; there is no parallel or duplicate report table.
- **One amount, one status per bill.** `Bill.total_amount` is the sum of its
  items; `Bill.status` is a single enum. No redundant amount or status columns.
- **Derived values are computed, not stored.** Order-level figures such as
  "how many stones are identified" are calculated from the stones, so they can
  never fall out of sync.
- **Reference data lives in `core`** as lookup tables; workflow states are
  code-defined enums (see [enums vs lookups](#module-core)).
- **Certificates snapshot their data on purpose.** A certificate freezes the
  stone's details at issue time (`*_snapshot` fields), so later edits to the
  report never change an issued certificate. This is the one intentional
  denormalization.
>
> Conventions in this doc:
> `PK` primary key · `FK→X` foreign key to X · `UQ` unique · `?` nullable/optional.
> Every FK notes its `on_delete` behavior. **Every CRUD table inherits the six
> audit columns from `core.BaseModel`** (below); they are not repeated in each
> table's column list.

---

## Base class & audit columns

Every table on which records are created, updated, or deleted inherits from one
abstract base, so the audit columns are defined once and maintained in one place.

**`core.BaseModel`** (abstract — no table of its own):

| Column | Type | Notes |
| --- | --- | --- |
| created_at | DateTime | `auto_now_add` |
| created_by | FK→User (SET_NULL, ?) | set in the service layer |
| updated_at | DateTime | `auto_now` |
| updated_by | FK→User (SET_NULL, ?) | set in the service layer |
| deleted_at | DateTime (?) | **null = live row; set = soft-deleted** |
| deleted_by | FK→User (SET_NULL, ?) | who soft-deleted it |

### Soft delete — the project rule

**Records are never physically deleted.** `delete()` is overridden to set
`deleted_at`/`deleted_by` instead of removing the row; `restore()` clears them.

| Manager | Returns |
| --- | --- |
| `objects` (default) | live rows only (`deleted_at IS NULL`) |
| `all_objects` | every row, including soft-deleted (for admin/audit) |

### Three rules this forces (must be honored in code)

1. **Unique constraints are scoped to live rows.** A soft-deleted row still
   holds its unique values, which would block re-creating them. Every unique
   constraint uses a **partial index** `WHERE deleted_at IS NULL` (Django:
   `UniqueConstraint(..., condition=Q(deleted_at__isnull=True))`).
2. **Cascades are handled in the service layer.** DB-level `on_delete` only
   fires on a real `DELETE`, which never happens. Deleting a parent must
   soft-delete its children explicitly in a service, inside a transaction.
3. **`created_by` / `updated_by` / `deleted_by` are set by services**, not the
   model — Django models don't know the request user. Pass the acting user into
   the service call.

### Append-only tables (exception)

`StatusHistory` and `CertificateAccessLog` are **immutable audit records** —
they are only ever inserted, never updated or deleted. They carry `created_at`
(+ actor) but **not** the soft-delete columns.

### Soft delete vs. `is_active` on lookups

Reference tables carry **both**, with distinct meaning:
`is_active = false` hides a value from new dropdowns while keeping existing
references valid; `deleted_at` removes it from use entirely. Prefer deactivating
reference data over deleting it.

---

## Module: `core`

### Enums *(defined in code, not tables)*

A reference value is an **enum** when it's small, fixed/scientific, has no extra
columns, and no one adds to it at runtime. Enums have no join cost.

| Enum | Values | Notes |
| --- | --- | --- |
| **StoneStatus** | received · under_identification · in_production · billed · paid · certified · ready_for_collection · collected · on_hold · cancelled | workflow stages **(open: B5)** |
| **Transparency** | transparent · semi_transparent · translucent · opaque | |
| **OpticCharacter** | isotropic · uniaxial ± · biaxial ± · aggregate | |
| **WeightUnit** | carat (ct) · gram (g) | symbol mapped in code **(open: B3)** |
| **Color** | colorless, white, red, pink, orange, yellow, green, blue, violet, purple, brown, black, gray, multicolor | draft — team to confirm list |
| **Treatment** | none, heated, oiled, dyed, irradiated, fracture_filled, bleached, impregnated | draft — team to confirm list |

### Reference lookups *(tables)*

A reference value is a **table** when it grows, carries metadata, has
relationships, or is large. Admin-managed (decision A3).

| Table | Columns | Why a table |
| --- | --- | --- |
| **StoneType** | id `PK` · name · category (`precious`/`semi_precious`/`diamond`) · is_active | has metadata; drives pricing (A6) |
| **Species** | id `PK` · name · is_active | large, growing; Variety FKs it |
| **Variety** | id `PK` · name · species `FK→Species (PROTECT)` · is_active | relationship + large |
| **Origin** | id `PK` · name · is_active | many mines/regions, grows |
| **ShapeCut** | id `PK` · name · is_active | staff add new cuts |
| **Instrument** | id `PK` · name · is_active | referenced with readings by `InstrumentUsed` |

*(All lookup tables also carry the `core.BaseModel` audit columns.)*

### StonePrice
The price list — `stone type → rate`. **(open: B2 flat vs tiered)**

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone_type | FK→StoneType (PROTECT) `UQ` | one active rate per type |
| price_per_unit | Decimal(15,2) | rate per weight unit |
| unit | WeightUnit (enum) | the unit the rate is per **(open: B3)** |
| is_active | bool | |

> If pricing is tiered (B2), replace `price_per_unit` with a related
> `StonePriceBand` table (min_weight, max_weight?, rate).

---

## Module: `accounts`

### User  *(extends AbstractUser — already scaffolded)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| username, email, password, is_active, is_staff… | (from AbstractUser) | |

**Roles & permissions use Django's built-in auth** — a `Group` is a role, and
permissions attach to groups. No custom role table. Roles (receptionist,
gemmologist, production, accountant, admin) are seeded as Groups. If "one role
per user" must be enforced, do it by convention (one group per user) rather than
a new model. *(Resolves C5.)*

---

## Module: `orders`

### Customer  **(open: C1 — identity fields)**

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| first_name | Char(100) | |
| middle_name | Char(100, blank) | optional |
| last_name | Char(100) | |
| phone | Char(20) | |
| *(full_name)* | — | a computed `@property`, not stored |
| email | Email (blank) | |
| id_number | Char(50, blank) | national/tax ID **(open: C1)** |
| address | Char(255, blank) | |

### Order

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| reference_no | Char(30) `UQ` | human-readable, e.g. `ORD-2026-0042` **(open: C6)** |
| customer | FK→Customer (PROTECT) | `related_name="orders"` |
| received_date | Date | |
| stone_count | PositiveInteger | how many stones the customer submitted (recorded at reception) |
| created_by | FK→User (SET_NULL, ?) | receptionist |

> **Reception records only the count.** The receptionist does not examine stones
> — they enter `stone_count`. Individual `Stone` records are created later, during
> identification, when the gemmologist records each stone's properties.
>
> Order has **no status field** — status lives on each Stone (decision A7).

### Stone  *(one record per physical stone — created at identification)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| order | FK→Order (CASCADE) | `related_name="stones"` |
| label | Char(20) | e.g. "A", "B" within the order |
| stone_type | FK→core.StoneType (PROTECT) | set at identification |
| weight | Decimal(10,3) | set at identification **(open: B3 — unit)** |
| weight_unit | Char (WeightUnit enum) | |
| status | Char (StoneStatus enum) | default `received` |

> A `Stone` exists once a gemmologist registers it (service `add_stone`), which
> refuses to exceed the order's `stone_count`. One record per physical stone (no
> parcels).

### StatusHistory  *(audit trail — decision A9)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone | FK→Stone (CASCADE) | `related_name="status_history"` |
| from_status | Char (StoneStatus, blank) | empty on first entry |
| to_status | Char (StoneStatus) | |
| changed_by | FK→User (SET_NULL, ?) | |
| changed_at | DateTime | `auto_now_add` |
| note | Char(255, blank) | e.g. "sent to lapidary" |

---

## Module: `identification`

### IdentificationReport  *(one per stone — decision A2)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone | OneToOne→orders.Stone (CASCADE) | one report per stone |
| species | FK→core.Species (PROTECT, ?) | |
| variety | FK→core.Variety (PROTECT, ?) | |
| origin | FK→core.Origin (PROTECT, ?) | |
| shape_cut | FK→core.ShapeCut (PROTECT, ?) | |
| color | Color (enum, ?) | |
| transparency | Transparency (enum, ?) | |
| treatment | Treatment (enum, ?) | |
| optic_character | OpticCharacter (enum, ?) | |
| conclusion | Text (blank) | gemmologist's finding/summary |
| is_finalized | bool | locks the report **(open: C4)** |
| completed_at | DateTime (?) | |

### InstrumentUsed  *(which instruments were used on a report)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| report | FK→IdentificationReport (CASCADE) | `related_name="instruments_used"` |
| instrument | FK→core.Instrument (PROTECT) | |
| reading | Char(100, blank) | measured value |

---

## Module: `production`  *(one model, type field — decision A10)*

### Production

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone | FK→orders.Stone (CASCADE) | `related_name="productions"` — **many? (open: B1)** |
| type | Char (enum: sonara/carving/lapidary) | the workshop |
| assigned_to | FK→User (SET_NULL, ?) | production staff |
| started_at | DateTime (?) | |
| finished_at | DateTime (?) | |
| qa_result | Char (enum: pending/passed/failed) | quality assurance |
| qa_by | FK→User (SET_NULL, ?) | |
| notes | Text (blank) | |

> FK (not OneToOne) allows multiple production steps per stone **if B1 = yes**.
> If B1 = one step only, change to OneToOne.

---

## Module: `billing`

### ServiceProvider  *(GePG configuration)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| sp_code | Char(20) `UQ` | |
| name | Char(255) | |
| group_code, sys_code | Char (blank) | |
| is_active | bool | |

### Bill  *(one per order — decision A4)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| order | OneToOne→orders.Order (PROTECT) | one bill per order |
| bill_number | Char(50) `UQ` | internal reference |
| control_number | Char(50) `UQ` (?) | from GePG |
| service_provider | FK→ServiceProvider (PROTECT) | |
| total_amount | Decimal(15,2) | = Σ BillItem.amount (snapshot) |
| currency | Char(3) | default "TZS" |
| status | Char (enum: pending/paid/partially_paid/cancelled/expired) | **(open: C2)** |
| issued_at | DateTime (?) | |
| due_date | Date (?) | |

### BillItem  *(one per stone; price snapshotted — see §Stage 4)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| bill | FK→Bill (CASCADE) | `related_name="items"` |
| stone | FK→orders.Stone (PROTECT) | |
| description | Char(255) | e.g. "Ruby, 3.20 ct" |
| unit_price | Decimal(15,2) | **snapshot** of rate used |
| weight | Decimal(10,3) | **snapshot** at billing time |
| amount | Decimal(15,2) | **snapshot** = unit_price × weight |

> The three snapshot columns freeze the calculation so later `StonePrice`
> changes never alter an issued bill.

### Payment

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| bill | FK→Bill (PROTECT) | `related_name="payments"` |
| amount | Decimal(15,2) | supports partial payments **(open: C2)** |
| paid_at | DateTime | |
| channel | Char(50) | GePG / bank / cash **(open: C2)** |
| reference | Char(100, blank) | transaction ref |

---

## Module: `certificates`  *(one per stone — decision A5)*

### Certificate

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone | OneToOne→orders.Stone (PROTECT) | one certificate per stone |
| report | FK→identification.IdentificationReport (PROTECT) | source data |
| certificate_no | Char(30) `UQ` | human-readable **(open: C6)** |
| verification_token | Char(64) `UQ` | for the public QR URL |
| issued_at | DateTime | |
| issued_by | FK→User (SET_NULL, ?) | |
| status | Char (enum: issued/revoked/reissued) | **(open: C3)** |

### CertificateAccessLog  *(who scanned/verified a certificate)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| certificate | FK→Certificate (CASCADE) | `related_name="access_logs"` |
| accessed_at | DateTime | `auto_now_add` |
| ip_address | GenericIPAddress (?) | |
| user_agent | Char(255, blank) | |

---

## Full relationship map

```
accounts.User ─┐ (created_by / assigned_to / changed_by on many tables)
              │
orders.Customer 1─* orders.Order 1─1 billing.Bill 1─* billing.BillItem *─1 orders.Stone
                          │                                                      │
                          1                                                      │
                          *                                                      │
                    orders.Stone ─────────────────────────────────────────────┘
                          │  status (enum) + orders.StatusHistory (audit)
                          │
        ┌─────────────────┼──────────────────┬──────────────────┐
        1                 *(B1?)              1                  1
identification.        production.        certificates.     (billing via
IdentificationReport   Production         Certificate        BillItem above)
        │                                      │
        *─ FK → core lookups                   └─ FK → IdentificationReport
        1─* InstrumentUsed
                                     billing.Bill 1─* billing.Payment
                                     certificates.Certificate 1─* CertificateAccessLog
```

---

## Design rules enforced in this schema

1. **Money is `Decimal(15,2)`** everywhere — never float.
2. **Bill line items snapshot** unit_price/weight/amount — issued bills are immutable.
3. **Status on Stone, not Order** — stones progress independently (A7).
4. **`PROTECT` on reference/master data FKs** — you can't delete a StoneType that
   bills or reports point to; `CASCADE` only where children are truly owned
   (Stone→Order, BillItem→Bill, StatusHistory→Stone).
5. **Reference tables carry `is_active`** — deactivate instead of delete, so
   history stays intact.
6. **Every FK gets a `related_name`**; nullable FKs to User use `SET_NULL` so
   deleting a user never deletes business records.
7. **Soft delete everywhere** — no row is ever physically deleted. All CRUD
   tables inherit `core.BaseModel` (six audit columns); `delete()` sets
   `deleted_at`. Unique constraints are partial (`WHERE deleted_at IS NULL`) and
   parent deletes cascade to children in the service layer. `on_delete` values
   above describe the *intended* cascade relationship — enforced softly, since
   real DB deletes never occur.
8. **`is_active` ≠ deleted** — reference data is deactivated (hidden from new
   entries) rather than deleted where possible.

---

## Blocked-on decisions (schema will change)

| Open Q | Column(s) affected |
| --- | --- |
| B1 | `Production.stone` — FK (many) vs OneToOne (one) |
| B2 | `StonePrice` — single rate vs tiered `StonePriceBand` |
| B3 | weight units throughout (`SiUnit` usage) |
| B4 | whether Certificate creation checks Bill.status = paid |
| B5 | `StoneStatus` enum values |
| C1 | `Customer` identity fields |
| C2 | `Bill.status`, `Payment.channel`, partial-payment rules |
| C3 | `Certificate.status` (revoke/reissue) |
| C4 | `IdentificationReport.is_finalized` locking rule |
| ~~C5~~ | ✅ Resolved — roles = Django Groups; no custom table. Still need the team to name the roles and which stages each may act on. |
| C6 | reference-number formats (`Order`, `Certificate`) |
