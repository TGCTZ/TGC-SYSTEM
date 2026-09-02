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
  | `billing.generate_bill` | Bill |
  | `certificates.issue_certificate`, `certificates.revoke_certificate` | Certificate |
  | `accounts.verify_user`, `accounts.approve_user` | User |

## Roles

Four seeded Groups: `receptionist`, `gemmologist`, `accountant`, `administrator`.
The Group→permission mapping for these is the version-controlled baseline in
[`apps/accounts/roles.py`](../../apps/accounts/roles.py) (`ROLE_PERMISSIONS`),
where `administrator` also holds the `auth.*_group` and `accounts.*_user`
permissions that gate the portals below.

> **Reference data:** the gemmologist gets **view** on every lookup
> (`StoneType`, `Species`, `Variety`, `Color`, `Origin`, `ShapeCut`,
> `Instrument`) and the administrator gets full CRUD on them + `StonePrice` —
> assembled from the `_REFERENCE_VIEW` / `_REFERENCE_MANAGE` sets in `roles.py`.

Seed or refresh the baseline Groups (idempotent):

```bash
python manage.py setup_roles
```

Beyond the baseline, roles are managed at runtime through the **roles & permissions
portal** (`/backoffice/roles/`, `backoffice` module): create Groups and toggle their
permissions on a per-model matrix, and add/remove members. Assign users to groups
there or in the **users module** (`/users/`) — the Django admin remains available too.

> The matrix governs **business** permissions (the project's own apps). Infrastructure
> permissions a role holds (e.g. `auth.*_group`) are preserved across edits but not
> shown, so editing a role through the portal never silently drops them.

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
