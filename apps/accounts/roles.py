"""Role definitions and their permission sets.

Roles are Django Groups. ``ROLE_PERMISSIONS`` maps each group to the permission
labels it grants, and is the version-controlled source of truth applied by the
``setup_roles`` management command. Mapping is provisional (domain question C5).
"""

# Role (Group) names.
RECEPTIONIST = "receptionist"
GEMMOLOGIST = "gemmologist"
ACCOUNTANT = "accountant"
ADMINISTRATOR = "administrator"

# Reference lookups an operator selects from during data entry (view-only).
_REFERENCE_VIEW = [
    "core.view_stonetype",
    "core.view_species",
    "core.view_variety",
    "core.view_color",
    "core.view_origin",
    "core.view_shapecut",
    "core.view_instrument",
]

# Full CRUD on reference data + pricing, for the administrator.
_REFERENCE_MANAGE = [
    f"core.{action}_{model}"
    for model in (
        "stonetype",
        "species",
        "variety",
        "color",
        "origin",
        "shapecut",
        "instrument",
        "stoneprice",
    )
    for action in ("add", "change", "delete", "view")
]

ROLE_PERMISSIONS: dict[str, list[str]] = {
    RECEPTIONIST: [
        "orders.add_customer",
        "orders.change_customer",
        "orders.view_customer",
        "orders.add_order",
        "orders.view_order",
        "orders.add_stone",
        "orders.view_stone",
        "orders.transition_stone",
        "certificates.view_certificate",
    ],
    GEMMOLOGIST: [
        "orders.view_stone",
        "orders.transition_stone",
        "identification.add_identificationreport",
        "identification.change_identificationreport",
        "identification.view_identificationreport",
        "identification.finalize_report",
        "certificates.view_certificate",
        "certificates.issue_certificate",
        *_REFERENCE_VIEW,
    ],
    ACCOUNTANT: [
        "orders.view_order",
        "orders.view_stone",
        "billing.view_bill",
        "billing.generate_bill",
        "billing.view_payment",
    ],
    ADMINISTRATOR: [
        *_REFERENCE_MANAGE,
        "accounts.add_user",
        "accounts.change_user",
        "accounts.view_user",
        "accounts.delete_user",
        "accounts.verify_user",
        "accounts.approve_user",
        # Roles & permissions portal (Groups) at /manage/roles/.
        "auth.view_group",
        "auth.add_group",
        "auth.change_group",
        "auth.delete_group",
        # Certificates.
        "certificates.view_certificate",
        "certificates.issue_certificate",
        "certificates.revoke_certificate",
    ],
}
