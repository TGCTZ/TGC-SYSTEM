# Business Workflow

> How a customer's stones move through TGC-SYSTEM, end to end — the stages, who
> acts at each one, and how a stone's status changes along the way.
>
> This describes the **business process**, not the code. For the data model see
> the ERD in [`domain-questions.md`](domain-questions.md); for open decisions
> that affect this flow, see Parts B and C of that same file.
>
> Items marked **(assumption)** depend on a question not yet answered by the
> team — treat them as provisional.

---

## 1. The process at a glance

```
 ┌────────────┐   ┌────────────────┐   ┌────────────┐   ┌──────────┐   ┌──────────────┐
 │ RECEPTION  │──▶│ IDENTIFICATION │──▶│ PRODUCTION │──▶│ BILLING  │──▶│ CERTIFICATE  │
 │            │   │  & FINDINGS    │   │ (optional) │   │ & PAYMENT│   │  & HANDOVER  │
 └────────────┘   └────────────────┘   └────────────┘   └──────────┘   └──────────────┘
   receptionist      gemmologist        production staff   accountant      receptionist
```

- An **Order** groups one or many **Stones** brought by one **Customer**.
- Each **Stone** flows through the pipeline **independently** — one stone may be
  certified while another in the same order is still in production.
- Billing happens once **per order**; certificates are issued **per stone**.

---

## 2. Roles (actors)

> **(assumption)** — exact roles and their permissions are open question C5.
> This is the working set implied by the workflow.

| Role | Responsible for |
| --- | --- |
| **Receptionist** | Registers customers, creates orders, logs stones, hands over finished certificates. |
| **Gemmologist** | Examines each stone and produces its identification report. |
| **Production staff** | Carries out sonara / carving / lapidary work and records QA. |
| **Accountant** | Generates bills, handles GePG, confirms payment. |
| **Administrator** | Manages reference data (lookups, prices) and users. |

---

## 3. Stage by stage

### Stage 1 — Reception
**Who:** Receptionist

1. Register the **Customer**.
2. Create an **Order** for the visit, recording only **how many stones** the
   customer submitted (`stone_count`).

The receptionist does **not** examine or measure stones — no type, weight, or
other property is recorded here. Individual stone records are created later, at
identification.

**Result:** an Order with a `stone_count`; no `Stone` records yet.

---

### Stage 2 — Identification & Findings
**Who:** Gemmologist

1. Take a physical stone and **register it** on the order (`add_stone`) —
   recording its stone type, weight, and unit. This creates the `Stone` record
   (`received`). The system caps registrations at the order's `stone_count`.
2. Record findings on the stone's **Identification Report** — species, variety,
   color, transparency, origin, treatment, shape/cut, optic character, and any
   instrument readings (all chosen from admin-managed reference lists).
3. Complete the report.

**Result:** each submitted stone becomes a `Stone` record with one completed
identification report; status advances.

> **(assumption)** Whether a report can still be edited after later stages is
> open question C4.

---

### Stage 3 — Production *(optional)*
**Who:** Production staff

1. If a stone needs processing, a **Production** record is opened with its
   **type** — sonara, carving, or lapidary.
2. Record assignment, start/finish, quality-assurance result, and notes.

> **(assumption)** Whether a stone may go through **more than one** production
> step (e.g. lapidary then carving) is open question B1. Whether a stone may
> **skip** production entirely — going straight to billing — is open question B6.

**Result:** processed stones have one or more production records; status advances.

---

### Stage 4 — Billing & Payment
**Who:** Accountant

1. Once an order's stones are ready to bill, generate **one Bill for the Order**.
2. The bill has a **line item per stone**, priced by **stone type × weight**.
   The computed amount and the unit price used are **frozen onto the line item**
   at billing time, so later price-list changes never alter an issued bill.
3. Submit the bill to **GePG**, which returns a **control number**.
4. The customer pays; payment is confirmed (synchronously or via GePG callback).

> **(assumption)** Pricing shape (flat vs tiered) is B2; the unit of weight is
> B3; partial payments and bill cancellation/reissue are C2.

**Result:** the order is billed and, once settled, marked paid.

---

### Stage 5 — Certificate & Handover
**Who:** Receptionist (issue/handover), system (verification)

1. A **Certificate is issued per stone**, carrying its identification results.
2. Each certificate has a **QR code** linking to a public verification page.
3. The customer collects the certified stones; handover is recorded.

> **(assumption)** Whether payment must be **complete before** a certificate is
> issued is open question B4. Certificate re-issuance and revocation are C3.

**Result:** each stone is certified and, once collected, closed out.

---

## 4. Stone status lifecycle

Each stone carries its **own status** (a fixed set defined in code), and every
change is written to a **status-history audit trail** recording *who* moved it,
*from* which status, *to* which status, *when*, and an optional note.

> **(assumption)** The exact status list is open question B5. Draft below —
> to be confirmed by the team.

```
received
   │
   ▼
under_identification
   │
   ▼
in_production ····· (skippable — B6)
   │
   ▼
billed
   │
   ▼
paid
   │
   ▼
certified
   │
   ▼
ready_for_collection
   │
   ▼
collected

  side states:  on_hold   ·   cancelled
```

**Audit trail — every transition records:**

| Field | Example |
| --- | --- |
| Stone | Stone #A of Order ORD-2026-0042 |
| From status | `under_identification` |
| To status | `in_production` |
| Changed by | gemmologist J. Doe |
| Changed at | 2026-08-27 14:05 |
| Note | "sent to lapidary" |

---

## 5. Key business rules (confirmed)

1. **Reception records only a stone count** (`stone_count`); stones are created
   later, at identification, one record per physical stone.
2. A **report is produced per stone**.
3. Reference data (colors, species, treatments, prices, …) is **admin-managed**;
   staff select from fixed lists, not free text.
4. **One Bill per Order** — the customer pays once for the whole batch.
5. Pricing is driven by **stone type and weight**.
6. A **certificate is issued per stone**.
7. Each **stone moves independently** through the pipeline.
8. Workflow **stages are fixed** (defined in code, not staff-editable).
9. A **status audit trail is mandatory** — every transition is logged.
10. Production is **one model with a type field** (sonara / carving / lapidary).

*(These are the confirmed decisions — Part A of `domain-questions.md`.)*

---

## 6. Open points that change this workflow

Answers to these will update the stages above. See `domain-questions.md`.

| Ref | Question | Affects |
| --- | --- | --- |
| B1 | Multiple production steps per stone? | Stage 3 |
| B2 | Flat vs tiered pricing? | Stage 4 |
| B3 | Weight unit (carats/grams)? | Stages 1, 4 |
| B4 | Must a bill be paid before certification? | Stages 4→5 |
| B5 | Exact status list? | §4 lifecycle |
| B6 | Can stones skip production? | Stage 3 |
| C2 | Partial payments, bill cancellation? | Stage 4 |
| C3 | Certificate re-issue / revocation? | Stage 5 |
| C4 | Report editable after billing/cert? | Stage 2 |
| C5 | Roles and permissions? | §2 actors |
| C6 | Human-readable order/certificate numbers? | Stages 1, 5 |
```
