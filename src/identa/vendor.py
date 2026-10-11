"""What a vendor file contains, derived only from the intent so it is reproducible."""

from __future__ import annotations

import yaml


def render_vendor_file(company_id: int | str, name: str, domain: str) -> str:
    doc = {"crustdata_company_id": int(company_id), "name": name, "domain": domain}
    return yaml.safe_dump(doc, sort_keys=True, allow_unicode=True)


def pr_title(name: str, domain: str) -> str:
    return f"Add vendor {name} ({domain})"
