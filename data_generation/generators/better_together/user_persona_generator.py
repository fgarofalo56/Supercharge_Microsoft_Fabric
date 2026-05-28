"""
User Persona Generator
======================

Generates synthetic Entra ID users + group assignments for the security
automation notebooks in tutorial 57. These are NOT real users — they're
fabricated names with deterministic UPNs in a sample domain so the security
notebooks can be re-run idempotently against a sandbox tenant.

Personas (drive every defense-in-depth example in the tutorial):
    - regional_sales_manager   one per region, sees only own region (RLS)
    - regional_analyst         one per region, read-only via SQL endpoint
    - finance_analyst          sees revenue across regions, PII masked (CLS)
    - exec                     sees everything
    - audit                    read-only on audit views, no row data
    - data_engineer            full lakehouse write
    - service_principal        non-human, owns scheduled refresh
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from data_generation.generators.base_generator import BaseGenerator

from .retail_generator import REGIONS

PERSONAS: tuple[dict[str, Any], ...] = (
    {
        "persona": "regional_sales_manager",
        "per_region": True,
        "group": "grp-sales-mgr-{region}",
    },
    {
        "persona": "regional_analyst",
        "per_region": True,
        "group": "grp-analyst-{region}",
    },
    {"persona": "finance_analyst", "per_region": False, "group": "grp-finance"},
    {"persona": "exec", "per_region": False, "group": "grp-exec"},
    {"persona": "audit", "per_region": False, "group": "grp-audit"},
    {"persona": "data_engineer", "per_region": False, "group": "grp-data-engineer"},
)


class UserPersonaGenerator(BaseGenerator):
    """Generate synthetic users + group assignments for security automation."""

    def __init__(
        self,
        seed: int | None = 57,
        domain: str = "btdemo.example.com",
    ):
        super().__init__(seed=seed)
        self.domain = domain

    def generate_record(self) -> dict[str, Any]:
        raise NotImplementedError(
            "Use generate_all() — emits users + groups + memberships."
        )

    def _make_user(
        self, persona: str, group_name: str, region: str | None
    ) -> dict[str, Any]:
        first = self.faker.first_name()
        last = self.faker.last_name()
        suffix = f"-{region.lower()}" if region else ""
        upn = f"{first.lower()}.{last.lower()}{suffix}@{self.domain}"
        return {
            "user_id": f"U-{persona}-{(region or 'global').lower()}-{self.faker.uuid4()[:8]}",
            "upn": upn,
            "display_name": f"{first} {last}",
            "first_name": first,
            "last_name": last,
            "persona": persona,
            "region": region or "ALL",
            "group_name": group_name,
            "is_service_principal": False,
        }

    def generate_all(self) -> dict[str, pd.DataFrame]:
        users: list[dict[str, Any]] = []
        groups: set[str] = set()

        for persona in PERSONAS:
            if persona["per_region"]:
                for region in REGIONS:
                    group = persona["group"].format(region=region.lower())
                    groups.add(group)
                    users.append(self._make_user(persona["persona"], group, region))
            else:
                group = persona["group"]
                groups.add(group)
                users.append(self._make_user(persona["persona"], group, None))

        users.append(
            {
                "user_id": "SP-better-together-refresh",
                "upn": "sp-better-together-refresh@btdemo.example.com",
                "display_name": "SP — Semantic Model Refresh",
                "first_name": "ServicePrincipal",
                "last_name": "Refresh",
                "persona": "service_principal",
                "region": "ALL",
                "group_name": "grp-service-principals",
                "is_service_principal": True,
            }
        )
        groups.add("grp-service-principals")

        groups_df = pd.DataFrame(
            [
                {
                    "group_name": g,
                    "description": f"Tutorial 57 synthetic group: {g}",
                }
                for g in sorted(groups)
            ]
        )

        return {
            "users": pd.DataFrame(users),
            "groups": groups_df,
        }
