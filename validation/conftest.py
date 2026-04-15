"""
validation/conftest.py
======================
Session-scoped fixtures shared across all validation test suites.
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_hash_salt() -> None:
    """Ensure FABRIC_POC_HASH_SALT is set for the entire test session.

    The data generators require this environment variable when hashing PII
    (e.g. SSNs). Without it, generators that call ``get_hash_salt()`` will
    raise a ``ValueError``.  In CI the variable is injected via GitHub Actions
    secrets; locally it falls back to the sentinel value below so that no real
    production salt is ever embedded in source control.
    """
    if not os.environ.get("FABRIC_POC_HASH_SALT"):
        os.environ["FABRIC_POC_HASH_SALT"] = "test-salt-do-not-use-in-production"
