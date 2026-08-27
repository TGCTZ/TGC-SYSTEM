# Domain & Business Rules — Questions for the Team

> Purpose: pin down the business rules that drive the database design **before**
> models are written. Part A records decisions already made. Part B lists open
> questions that still need an answer. Part C raises questions we haven't
> discussed yet but the team should consider.
>
> Please review Part B and Part C and fill in answers. Each answer directly
> shapes the database schema.

---

## The workflow (shared understanding)

```
Customer brings stones
      ↓
RECEPTION      → an Order is created, containing one or more Stones
      ↓
IDENTIFICATION → a gemmologist examines each stone → a report per stone
      ↓
PRODUCTION     → optional processing: sonara / carving / lapidary
      ↓
BILLING        → one Bill per Order; GePG control number; customer pays
      ↓
CERTIFICATE    → a certificate is issued per stone (with QR verification)
```

---

## Part A — Decisions already made ✅

| # | Question | Decision |
| --- | --- | --- |
| A1 | Does an order contain one stone or many? | **One or a batch of many stones**, all under a single order. |
| A2 | Is a gemmological report produced per stone or per order? | **Per stone** — each stone gets its own identification report. |
| A3 | Is the reference data (colors, species, treatments, etc.) fixed or user-editable during data entry? | **Stable, admin-managed lookup lists** — staff choose from dropdowns; they are not added ad hoc during data entry. |
| A4 | Is billing per order or per stone? | **One Bill per Order** — the customer pays once for the whole batch. |
| A5 | Is a certificate issued per order or per stone? | **Per stone** — each stone gets its own certificate and QR verification. |
| A6 | What determines a stone's price? | **Stone type and weight.** |
| A7 | Does each stone carry its own status, or does the whole order move together? | **Each stone has its own status** and progresses independently through the pipeline. |
| A8 | Are the workflow stages fixed or editable by staff? | **Fixed stages defined in code** — they rarely change; developers manage them. |
| A9 | Is a status audit trail needed? | **Yes — a full audit trail is a must** ("who moved this stone to which stage, and when"). |
| A10 | Is production one model or three separate ones? | **One Production model with a `type` field** (sonara / carving / lapidary) — they share the same shape of record. |

---

## Part B — Open questions (need answers) ❓

### B1. Can a stone go through **multiple** production steps?
Can one stone be processed more than once — e.g. lapidary **and then** carving —
or is it strictly **one production step per stone**?
- *If multiple:* a Stone can have many Production records.
- *If one:* a Stone has at most one Production record.

**Answer:**

---

### B2. Is pricing a **flat rate** or **tiered by weight**?
Price is `stone type × weight`. But how exactly?
- **Flat:** a single price-per-unit (per carat/gram) for each stone type. Total =
  `weight × rate`.
- **Tiered:** the rate changes across weight bands (e.g. first 5 ct at one rate,
  above 5 ct at another).

**Answer:**

---

### B3. What is the unit of weight — **carats or grams** (or both)?
Does the business price and record weight in **carats**, **grams**, or does it
vary by stone type? (The `SiUnit` reference table implies more than one unit —
confirm which units are actually in use.)

**Answer:**

---

### B4. Can a stone be **billed but not yet certified**, and vice versa?
Confirm the ordering rule between payment and certification:
- Must a Bill be **fully paid** before a certificate is issued?
- Or can certificates be issued independently of payment status?

**Answer:**

---

### B5. What are the exact **workflow stages** (the fixed status list)?
We need the definitive, ordered list of stone statuses to define in code.
Draft based on the workflow — **please correct/complete**:

```
1. received            (logged at reception)
2. under_identification
3. in_production        (optional)
4. billed
5. paid
6. certified
7. ready_for_collection
8. collected
   + cancelled / on_hold ?
```

**Answer / corrections:**

---

### B6. Can a stone **skip** stages?
Production is described as optional. Can a stone go straight from
identification → billing without production? Are any other stages skippable?

**Answer:**

---

## Part C — Questions we haven't discussed (please consider) 🔎

These weren't raised yet but affect the schema or business logic. Please weigh in.

### C1. Customer identity
What identifies a customer — name + phone, a national/tax ID, a company?
Can the **same customer** return for multiple orders (so we keep a customer
record), or is customer info captured **fresh per order**?

**Answer:**

---

### C2. GePG billing specifics
- Does every Bill go through GePG, or are there other payment methods?
- What happens on **partial payment** — is that a valid state, or must bills be
  paid in full?
- Can a Bill be **cancelled or reissued** after a control number is generated?

**Answer:**

---

### C3. Certificate re-issuance & revocation
- Can a certificate be **re-issued** (e.g. lost copy, correction)?
- Can a certificate be **revoked/invalidated** after issue? If so, the public QR
  verification must reflect that.

**Answer:**

---

### C4. Editing after the fact
Once a stone is billed or certified, can its identification report still be
**edited**? If reports are locked at some stage, we need to enforce that in the
model.

**Answer:**

---

### C5. Who can do what (roles)
The system has a custom user model. What **roles** exist (receptionist,
gemmologist, production staff, accountant, admin…), and which stages can each
role act on? This drives the permissions layer.

**Partly decided:** roles are implemented as **Django Groups** with attached
permissions — no custom role table. **Still needed from the team:** the
definitive list of roles and, for each, which stages/actions it may perform.

**Answer (roles & their permitted actions):**

---

### C6. Order / stone identifiers
- Does an Order need a **human-readable reference number** (e.g. `ORD-2026-0042`)?
  What format?
- Does each Stone/certificate need its own external-facing number?

**Answer:**

---

### C7. Data retention & history
Beyond the status audit trail, does the business need to keep a history of
**edits** to reports or bills (who changed a value and when), or is the status
trail sufficient?

**Answer:**

---

## Current draft data model (for reference)

This is the schema implied by the decisions in Part A. It will change based on
Part B and Part C answers.

```
Customer 1──< Order 1──1 Bill 1──< BillItem >──1 Stone
                 │                                  │
                 └──< Stone ───────────────────────┘
                        │  status (fixed enum) + StatusHistory (audit)
                        │
      ┌─────────────────┼──────────────────┐
      │ 1               │ 1..* (B1?)        │ 1
 IdentificationReport   Production        Certificate
 (per stone)            (type field)      (per stone)
      │
      └─ FKs → core lookups: StoneType, Species, Variety, Color,
               Transparency, Origin, Treatment, ShapeCut, OpticCharacter,
               SiUnit, Instrument, StonePrice
```
