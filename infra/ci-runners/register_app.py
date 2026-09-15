"""Security primitives for loopback GitHub App manifest registration."""

import re
import secrets
from urllib.parse import parse_qs

REPOSITORY = "https://github.com/fgarofalo56/Supercharge_Microsoft_Fabric"


def manifest(base_url: str) -> dict[str, object]:
    """Build a private runner App manifest without user OAuth permissions."""
    return {
        "name": "supercharge-fabric-azure-runners",
        "url": REPOSITORY,
        "public": False,
        "hook_attributes": {"url": base_url + "/unused", "active": False},
        "redirect_url": base_url + "/callback",
        "default_permissions": {"administration": "write", "actions": "read"},
        "default_events": [],
    }


def valid_callback(query: str, expected_state: str) -> str:
    """Reject missing, duplicate, malformed, or cross-session parameters."""
    params = parse_qs(query, keep_blank_values=True)
    if len(params.get("state", [])) != 1 or len(params.get("code", [])) != 1:
        raise ValueError("Invalid callback parameters")
    if not secrets.compare_digest(params["state"][0], expected_state):
        raise ValueError("Invalid callback state")
    code = params["code"][0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}", code):
        raise ValueError("Invalid callback code")
    return code
