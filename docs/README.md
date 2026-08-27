# Documentation Index

Docs are grouped by purpose. New folders are added as areas grow (e.g. `api/`,
`decisions/` for ADRs, `operations/` for deploy runbooks).

```
docs/
├── engineering/     how we build the system
├── domain/          what the system does (business rules & process)
└── database/        the data model (schema + DBML diagram)
```

## Engineering
| Doc | Purpose |
| --- | --- |
| [engineering/conventions.md](engineering/conventions.md) | Django & Python coding standards and the pre-commit checklist. |
| [engineering/project-structure.md](engineering/project-structure.md) | Annotated folder/file layout. |
| [engineering/modules.md](engineering/modules.md) | The module (app) catalog — names, responsibilities, and dependency layers. |

## Domain
| Doc | Purpose |
| --- | --- |
| [domain/business-workflow.md](domain/business-workflow.md) | End-to-end process: stages, roles, stone status lifecycle. |
| [domain/domain-questions.md](domain/domain-questions.md) | Business decisions — settled (Part A) and open (Parts B & C). |
| [domain/legacy-mifumo-modules.md](domain/legacy-mifumo-modules.md) | Inventory of the old TGC-MIFUMO system — modules, submodules, and how they map to the new apps. |

---

## Database
| Doc | Purpose |
| --- | --- |
| [database/data-model.md](database/data-model.md) | Human-readable schema — every table, column, type, relationship, and the normalization principles. |
| [database/schema.dbml](database/schema.dbml) | Machine-readable schema (DBML) — paste into dbdiagram.io for the ERD. Dependency-ordered. |

---

### Suggested reading order
1. `engineering/project-structure.md` — where things live
2. `engineering/conventions.md` — how we write code
3. `domain/business-workflow.md` — what the system does
4. `domain/domain-questions.md` — what's still being decided
