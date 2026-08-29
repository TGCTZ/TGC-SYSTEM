# Permissions

Access control uses Django's built-in auth: **roles are Groups**, and users get
permissions through their group(s). No custom role table.

## Permission vocabulary

- **Default CRUD** — Django creates `add/change/delete/view` per model.
- **Custom action permissions** — declared in each model's `Meta.permissions`
  for workflow actions that aren't plain CRUD:

  | Permission | Model |
  | --- | --- |
  | `orders.transition_stone` | Stone |
  | `identification.finalize_report` | IdentificationReport |
  | `production.record_qa` | Production |
  | `billing.generate_bill` | Bill |
  | `certificates.issue_certificate`, `certificates.revoke_certificate` | Certificate |
  | `accounts.verify_user`, `accounts.approve_user` | User |

## Roles

Five Groups: `receptionist`, `gemmologist`, `production`, `accountant`,
`administrator`. The Group→permission mapping is the source of truth in
[`apps/accounts/roles.py`](../../apps/accounts/roles.py) (`ROLE_PERMISSIONS`).

Seed or refresh them (idempotent):

```bash
python manage.py setup_roles
```

Assign users to groups in the Django admin (User → Permissions → Groups).

## Enforcement

Use the helper `apps/accounts/permissions.py`:

```python
from apps.accounts.permissions import require_permission

require_permission(user, "identification.finalize_report")
```

- `user is None` → trusted/system call (webhook, management command), allowed.
- Superusers always pass.
- Raises `PermissionDenied` otherwise.

**Current state:** permissions are defined and seeded, but enforcement is **not
yet wired into services**. It is added at each view/API entry point (which
carries a request user) as those are built.
