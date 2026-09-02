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
| **StoneStatus** | received · under_identification · billed · paid · certified · ready_for_collection · collected · on_hold · cancelled | workflow stages (B5 ✅) |
| **StoneCategory** | precious · semi_precious · diamond | pricing tier of a `StoneType` |
| **Transparency** | transparent · translucent · opaque | |
| **OpticCharacter** | SR · ADR · DR · AGG | stored as the short code; full label ("SR — Singly refractive") expands in code |
| **NatureType** | natural · synthetic · treated · enhanced · artificial | natural vs man-made/altered |
| **WeightUnit** | carat (ct) · gram (g) | symbol mapped in code |
| **Treatment** | none, heated, oiled, dyed, irradiated, fracture_filled, bleached, impregnated | draft — team to confirm list |
| **ColorGroup** | white_grey_black · purple_violet · red_pink · orange_yellow · green · blue | groups the `Color` lookup into `<optgroup>`s (see below) |

> **Color used to be an enum; it is now the `Color` lookup table** — the legacy
> finding form offers ~37 GIA-style values, too many (and too editable) for a
> code enum. See [Reference lookups](#reference-lookups-tables).

### Reference lookups *(tables)*

A reference value is a **table** when it grows, carries metadata, has
relationships, or is large. Admin-managed (decision A3).

| Table | Columns | Why a table |
| --- | --- | --- |
| **StoneType** | id `PK` · name · category (`precious`/`semi_precious`/`diamond`) · is_active | has metadata; drives pricing (A6) |
| **Species** | id `PK` · name · is_active | large, growing; Variety FKs it |
| **Variety** | id `PK` · name · species `FK→Species (PROTECT)` · is_active | relationship + large; unique on `(name, species)` |
| **Color** | id `PK` · name · group (`ColorGroup`) · is_active | ~37 GIA-style values, staff-editable; grouped into 6 families |
| **Origin** | id `PK` · name · is_active | many mines/regions, grows |
| **ShapeCut** | id `PK` · name · is_active | staff add new cuts |
| **Instrument** | id `PK` · name · is_active | referenced with readings by `InstrumentUsed` |

*(All lookup tables also carry the `core.BaseModel` audit columns.)*

**Color families (`ColorGroup`).** The `Color` lookup mirrors the legacy finding
form's grouped dropdown. The six groups and the ~37 seeded values are defined in
[`seed.py`](../../apps/core/management/commands/seed.py) (not inlined here, so the
list has one source of truth):

| Group | Example values |
| --- | --- |
| White/Grey/Black | Colourless, White, Grey, Black |
| Purple/Violet | Purple, Reddish Purple, Violetish Purple, Violet … |
| Red/Pink | Red, Orangy Red, Red-Orange, Pink, Brown … |
| Orange/Yellow | Orange, Yellowish Orange, Yellow, Greenish Yellow … |
| Green | Green, Yellowish Green, Bluish Green, Green-Blue … |
| Blue | Blue, Greenish Blue, Violetish Blue … |

### StonePrice
The price list — one **flat price per stone type** (B2 ✅ flat). Weight does **not**
affect the price.

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone_type | OneToOne→StoneType (PROTECT) `UQ` | one price per type |
| price | Decimal(12,2) | the flat amount charged for that type |

---

## Module: `accounts`

### User  *(extends AbstractUser — already scaffolded)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| username, email, password, is_active, is_staff… | (from AbstractUser) | |

**Roles & permissions use Django's built-in auth** — a `Group` is a role, and
permissions attach to groups. No custom role table. The four roles
(receptionist, gemmologist, accountant, administrator) are seeded as Groups. If
"one role per user" must be enforced, do it by convention (one group per user)
rather than a new model. *(Resolves C5.)*

---

## Module: `orders`

### Customer  **(open: C1 — identity fields)**

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| first_name | Char(100) | |
| middle_name | Char(100, blank) | optional |
| last_name | Char(100) | |
| phone | Char(20) `UQ` | unique among live rows |
| *(full_name)* | — | a computed `@property`, not stored |
| email | Email (blank) | |
| company_name | Char(255, blank) | for corporate customers |
| region | Char(100, blank) | |
| id_number | Char(50, blank) | national/tax ID **(open: C1)** |
| address | Char(255, blank) | |

### Order

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| reference_number | Char(30) `UQ` | human-readable, e.g. `ORD-2026-0042` **(open: C6)** |
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
| stone_type | FK→core.StoneType (PROTECT) | set when the type is identified (phase 1) |
| weight | Decimal(10,3) (?) | **null until findings** — recorded after payment |
| weight_unit | Char (WeightUnit enum) | default `carat` |
| status | Char (StoneStatus enum) | default `received`; indexed |

> A `Stone` exists once a gemmologist registers its **type** (service `add_stone`),
> which refuses to exceed the order's `stone_count`. One record per physical stone
> (no parcels). Its weight and full findings are filled in later, **after payment**
> (phase 2) — so `weight` is nullable.

### StatusHistory  *(audit trail — decision A9)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone | FK→Stone (CASCADE) | `related_name="status_history"` |
| from_status | Char (StoneStatus, blank) | empty on first entry |
| to_status | Char (StoneStatus) | |
| changed_by | FK→User (SET_NULL, ?) | |
| changed_at | DateTime | `auto_now_add` |
| note | Char(255, blank) | e.g. "type identified: Ruby" |

---

## Module: `identification`

### IdentificationReport  *(one per stone — decision A2)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone | OneToOne→orders.Stone (CASCADE) | one report per stone |
| report_number | Char(50) `UQ` | e.g. `RPT-00042` |
| species | FK→core.Species (PROTECT, ?) | |
| variety | FK→core.Variety (PROTECT, ?) | |
| origin | FK→core.Origin (PROTECT, ?) | |
| shape_cut | FK→core.ShapeCut (PROTECT, ?) | |
| color | FK→core.Color (SET_NULL, ?) | now a lookup, not an enum |
| nature_type | NatureType (enum, blank) | natural / synthetic / … |
| transparency | Transparency (enum, blank) | |
| treatment | Treatment (enum, blank) | |
| optic_character | OpticCharacter (enum, blank) | SR / ADR / DR / AGG |
| dimensions | Char(50, blank) | L x W x D in mm (free text) |
| refractive_index | Char(50, blank) | |
| specific_gravity | Decimal(10,3) (?) | |
| is_polished | bool | default false |
| conclusion | Text (blank) | gemmologist's finding/summary |
| is_finalized | bool | locks the report **(open: C4)** |
| identified_by | FK→User (SET_NULL, ?) | the gemmologist |
| identified_at | DateTime (?) | set on finalize |

### InstrumentUsed  *(which instruments were used on a report)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| report | FK→IdentificationReport (CASCADE) | `related_name="instruments_used"` |
| instrument | FK→core.Instrument (PROTECT) | |
| reading | Char(100, blank) | measured value |

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
| control_number | Char(50, blank) `UQ` | from GePG (unique when non-blank) |
| service_provider | FK→ServiceProvider (PROTECT, ?) | |
| total_amount | Decimal(15,2) | = Σ BillItem.amount (snapshot); default 0 |
| currency | Char(3) | default "TZS" |
| status | Char (BillStatus: pending/partially_paid/paid/cancelled/expired) | domain state **(open: C2)** |
| issued_at | DateTime (?) | |
| expiry_at | DateTime (?) | |
| due_date | Date (?) | |
| bill_type, pay_type | SmallInt | GePG submission params (default 1) |
| status_code, status_desc | Char (blank) | raw GePG gateway state |
| is_gepg_submitted | bool | default false |
| gepg_submitted_at | DateTime (?) | |

> `status` is the **domain** payment state; the `status_code`/`status_desc` and
> `gepg_*` columns track the raw gateway exchange separately.

### BillItem  *(one per stone; price snapshotted — see §Stage 4)*

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| bill | FK→Bill (CASCADE) | `related_name="items"` |
| stone | FK→orders.Stone (PROTECT) | `related_name="bill_items"` |
| description | Char(255) | e.g. the stone type name |
| unit_price | Decimal(15,2) | **snapshot** of the type's flat price |
| weight | Decimal(10,3) (?) | **snapshot** at billing (informational) |
| amount | Decimal(15,2) | **snapshot** = the flat price charged |
| gfs_code, item_ref | Char (blank) | GePG line references |

> The snapshot columns freeze the charge so later `StonePrice` changes never
> alter an issued bill. Pricing is **flat per stone type**, so `amount` equals the
> type's price (weight is recorded but does not change it).

### Payment  *(one row per GePG payment notification)*

Mirrors the GePG payment-notification message (`PmtTrxInf`): the system stores the
callback verbatim rather than a hand-rolled summary. Only the load-bearing columns
are listed; the rest map 1:1 to GePG fields.

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| bill | FK→Bill (PROTECT, ?) | `related_name="payments"` |
| cust_cntr_num | Char(12, blank) | customer control number |
| trx_id | Char(100, blank) `UQ` | GePG transaction id (unique when non-blank) |
| bill_amount / paid_amount | Decimal(15,2) (?) | billed vs actually paid |
| usd_pay_chnl | Char(50, blank) | payment channel used |
| trx_dt_tm | DateTime (?) | transaction timestamp |
| pyr_name / pyr_cell_num / pyr_email | Char (blank) | payer details |
| ack_id / ack_sts_code | Char (blank) | acknowledgement we returned |
| is_processed | bool | whether we've applied it to the bill |
| raw_request | Text (blank) | the raw callback payload |
| *(req_id, sp_code, gepg_bill_id, psp_code, …)* | Char | other GePG header/detail fields |

---

## Module: `certificates`  *(one per stone — decision A5)*

### Certificate

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| stone | OneToOne→orders.Stone (PROTECT) | one certificate per stone |
| report | FK→identification.IdentificationReport (PROTECT) | source data |
| certificate_number | Char(30) `UQ` | human-readable **(open: C6)** |
| verification_token | Char(64) `UQ` | for the public QR URL |
| stone_type_snapshot | Char(100) | **frozen** at issue |
| weight_snapshot | Decimal(10,3) | **frozen** at issue |
| color_snapshot | Char(100, blank) | **frozen** at issue |
| origin_snapshot | Char(100, blank) | **frozen** at issue |
| gemmologist | Char(100, blank) | **frozen** examiner name |
| qr_code | Char(100, blank) | stored QR artifact path |
| pdf_file | Char(100, blank) | stored PDF artifact path |
| status | Char (CertificateStatus: issued/revoked/reissued) | **(open: C3)** |
| issued_by | FK→User (SET_NULL, ?) | |
| issued_at | DateTime | |

> The `*_snapshot` + `gemmologist` columns freeze the report data at issue time,
> so later edits to the report never change an issued certificate (the one
> intentional denormalization).

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
        ┌─────────────────────────────────────┬──────────────────┐
        1                                     1                  1
identification.                          certificates.     (billing via
IdentificationReport                     Certificate        BillItem above)
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
| ~~B1~~ | ✅ Resolved — no production module in the current build. |
| ~~B2~~ | ✅ Resolved — pricing is flat per stone type (`StonePrice.price`). |
| ~~B3~~ | ✅ Resolved — weight unit is `carat`/`gram` (`WeightUnit`); no `SiUnit`. |
| B4 | whether Certificate creation checks Bill.status = paid |
| ~~B5~~ | ✅ Resolved — `StoneStatus` list settled (no `in_production`). |
| C1 | `Customer` identity fields |
| C2 | `Bill.status`, partial-payment rules |
| C3 | `Certificate.status` (revoke/reissue) |
| C4 | `IdentificationReport.is_finalized` locking rule |
| ~~C5~~ | ✅ Resolved — roles = Django Groups (receptionist, gemmologist, accountant, administrator); no custom table. |
| C6 | reference-number formats (`Order`, `Certificate`) |
