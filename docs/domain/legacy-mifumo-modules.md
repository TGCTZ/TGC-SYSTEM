# Legacy System (TGC-MIFUMO) — Module Inventory

> A map of the **existing** TGC-MIFUMO system: its main modules, their
> submodules, and what each does. Purpose: capture the functionality worth
> carrying forward, and expose the structural problems the rewrite fixes.
>
> This documents MIFUMO **as-is** — including its duplication and sprawl. For
> the target design, see [`business-workflow.md`](business-workflow.md) and
> [`domain-questions.md`](domain-questions.md).

---

## 1. Modules at a glance

MIFUMO has 12 active Django apps (plus 7 empty scaffolds). Grouped by what they
actually do:

| Module (app) | Role | Health |
| --- | --- | --- |
| `user_app` | Users **+** all reference/master data **+** workflow statuses | ⚠️ overloaded — 3 concerns in one app |
| `reception_app` | Orders & order items | ok |
| `gemmology_app` | Identification, findings, **certificates** | ⚠️ 3 concerns; 1300-line models |
| `billing_system_app` | GePG billing, payments, reconciliation | ⚠️ core billing, but huge |
| `production_home_app` | Production, supervision, QA, shop pricing | 🔴 the "god app" — does everything |
| `sonara_app` / `carving_app` / `lapidary_app` | Per-workshop QA | 🔴 near-duplicates of each other |
| `account_app` | Bill & payment viewing/entry | 🔴 duplicates billing |
| `report_app` | Report generation | ok (small) |
| `dashboard_app` / `home_app` | Landing/nav shells | ok (thin) |

---

## 2. Module → submodule breakdown

### `user_app` — Identity + Master Data + Workflow (overloaded)
Three unrelated concerns crammed together:

| Submodule | Contents |
| --- | --- |
| **User management** | `systemUser`, `User_Type`, `Role`, `Title`, `Department`, `SystemUserCategory`, login-attempt tracking, access-to-systems mapping. Files: `user_management.py`, `user_obj.py`, `setting.py`. |
| **Reference / master data** | `SiUnitTB`, `MetalStoneCategoryTB`, `MetalStoneTB`, `ColorTB`, `ShapeCutTB`, `TransparencyTB`, `OpticCharacterTB`, `GroupSpeciesTB`, `VarietyTB`, `TreatmentTB`, `OriginTB`, `InstrumentsTB`, `CurrencyTB`, `Workshop`, `Relationship`. |
| **Workflow status** | `Stage`, `Status`, `HistoryStatus`, `Action`, `Apllication_Type` (sic). |

> **Rewrite note:** splits into `accounts` (users/roles) + `core` (reference
> data) + a code-defined status enum. This is the single biggest untangling.

---

### `reception_app` — Orders
| Submodule | Contents |
| --- | --- |
| **Orders** | `OrderTB`, `OrderItemTB`, `StatusTB`. Files: `order.py`, `lib.py`. |
| **Order billing (stray)** | `BillTB` — a bill model living in reception (billing leaks in). |

**Feature surface:** create/update/search orders, order detail, update status,
`send_order_to_identification`, `generate_bill_for_order`.

> **Rewrite note:** `BillTB` here is duplication — billing belongs in one place.

---

### `gemmology_app` — Identification + Findings + Certificates
Three concerns; the largest models file in the system (1300+ lines).

| Submodule | Contents |
| --- | --- |
| **Pricing (stray)** | `ItemPrice`, `StonePrice` — pricing living in gemmology. |
| **Identification** | `IdentificationReportTB`, `StoneIdentification`, `InstrumentUsed`, `ItemTB`. File: `identification.py`. |
| **Findings** | `Finding`. File: `finding.py`. |
| **Certificates** | `Certificate`, `CertificateAccessLog`, `QRCodeCache`, public verification, PDF (`utils/pdf_generator.py`), QR generation. |
| **Signals** | `signals.py`. |

**Feature surface:** identifications CRUD, findings CRUD, certificate list /
PDF / QR / public verification / access logs, price lookup APIs, `generate_bill`.

> **Rewrite note:** splits into `gemmology` (identification + findings) and a
> dedicated `certificates` app. Pricing moves to `core`.

---

### `billing_system_app` — GePG Billing (core, but bloated)
The real billing engine — worth carrying forward, needs restructuring.

| Submodule | Contents |
| --- | --- |
| **Bills** | `Bill`, `BillItem`, `ServiceProvider`. |
| **Payments** | `Payment`. |
| **Reconciliation** | `Reconciliation`, `ReconciliationTransaction`, PDF/Excel export. |
| **Quotes** | `Quote`. |
| **GePG integration** | `gepg_service.py`, `crypto_utils.py` (digital signatures), `auth.py`, `services.py`, `utils.py`. |
| **Middleware** | `middleware.py` (`PaymentNotificationMiddleware`). |
| **API** | `views/payment_api.py`. |

**Feature surface:** payment/bill/cancel callbacks, control-number generation,
reconciliation flow, plus many `test_*` endpoints left in production URLs.

> **Rewrite note:** this becomes the single `billing` app. GePG client code
> moves to a `gateways/` subpackage; the `test_*` URLs are removed.

---

### `production_home_app` — the "god app" 🔴
By far the largest surface (~90 URL names). Does the work of several apps.

| Submodule | Contents |
| --- | --- |
| **Products/production** | `Product`, `ProductCategory`, `ProductionOrderTB`, `WorkshopFindingTB`. Files: `production.py`, `shop.py`. |
| **Supervision & assignment** | `SupervisorWorkshop`, `SupervisorAssignmentTB`, `AssigneeTB`. File: `supervisor.py`. |
| **Quality assurance** | `QualityAssuranceTB`, `QualityAssuranceLapidaryTB`. File: `qa.py`. |
| **Workshops** | `sonara.py`, `carving.py`, `lapidary.py` — parallel CRUD per workshop. |
| **Shop pricing** | set-price / qualified-price flow (`shop.py`). |
| **Billing (duplicate)** | `Bills`, `Payment` — *another* billing surface. Files: `account.py`, `lib.py`. |

**Feature surface:** product CRUD, supervisor assignment, staff selection,
QA add/edit/return, per-workshop CRUD (sonara/carving/lapidary), pricing,
bill/payment entry, `close_order`.

> **Rewrite note:** decomposes into `production` (one model, `type` field for
> sonara/carving/lapidary) + reuse of the shared `billing`. The duplicated
> billing/payment here is dropped.

---

### `sonara_app` / `carving_app` / `lapidary_app` — per-workshop QA 🔴
All three are **structurally identical** — same six URL names
(`quality_assurance_view/search/add/update/detail/update_status_product`), each
holding one QA model (`QualityAssuranceCarvingTB`, `QualityAssuranceLapidaryTB`,
etc.). `sonara_app` has no model at all.

> **Rewrite note:** the strongest evidence for **one `production` model with a
> `type` field**. Three apps → zero; the behavior is one shape.

---

### `account_app` — Bill & Payment desk 🔴 (duplicate)
| Submodule | Contents |
| --- | --- |
| **Bills** | view/add/update/detail, control-number request, cancel, invoice/receipt downloads. File: `bill.py`. |
| **Payments** | make/view/search/add/update payment. File: `payment.py`. |

No models of its own — it's a **third** billing/payment UI over other apps' data.

> **Rewrite note:** folds into the single `billing` app.

---

### `report_app` — Reporting
`ReportType`, `ReportTb`, `ReportAccessTb`. File: `report_obj.py`. Small, ok.

### `dashboard_app` / `home_app` — Shells
Landing pages and navigation/permission entry points. Thin — become the
`dashboard` entrypoint app.

---

## 3. Cross-cutting problems (why the rewrite)

### Billing is implemented in **five** places
`billing_system_app` (real), `reception_app.BillTB`, `gemmology_app.generate_bill`,
`production_home_app.Bills/Payment`, `account_app` (bill.py/payment.py).
→ **Target:** exactly one `billing` app.

### Quality assurance is implemented in **four** places
`production_home_app.qa`, `sonara_app`, `carving_app`, `lapidary_app` — identical shape.
→ **Target:** one `Production` model with QA fields and a `type`.

### `user_app` holds three unrelated concerns
Identity + reference data + workflow status.
→ **Target:** `accounts` + `core` + a status enum.

### Certificates buried inside `gemmology_app`
→ **Target:** a dedicated `certificates` app.

---

## 4. Legacy → target module map

| MIFUMO (as-is) | TGC-SYSTEM (target) |
| --- | --- |
| `user_app` (users/roles) | `accounts` |
| `user_app` (reference data, pricing) | `core` |
| `user_app` (status/stage) | `core` status enum + `reception.StatusHistory` |
| `reception_app` (orders) | `reception` |
| `reception_app.BillTB` | → `billing` |
| `gemmology_app` (identification, findings) | `gemmology` |
| `gemmology_app` (certificates) | `certificates` |
| `billing_system_app` | `billing` |
| `production_home_app` (production/QA/workshops) | `production` |
| `production_home_app` (bills/payments) | → `billing` |
| `sonara_app` / `carving_app` / `lapidary_app` | → `production` (type field) |
| `account_app` | → `billing` |
| `report_app` | `reporting` |
| `dashboard_app` / `home_app` | `dashboard` |

**Net: 19 apps (12 active + 7 empty) → ~8 focused apps.**
