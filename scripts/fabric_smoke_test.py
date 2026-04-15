"""Minimal smoke test: verify connectivity to a Microsoft Fabric workspace."""

from __future__ import annotations

import argparse
import sys

import requests
from azure.identity import DefaultAzureCredential

FABRIC_API = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"


def get_token() -> str:
    credential = DefaultAzureCredential()
    token = credential.get_token(FABRIC_SCOPE)
    return token.token


def list_items(workspace_id: str, token: str) -> requests.Response:
    url = f"{FABRIC_API}/workspaces/{workspace_id}/items"
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(url, headers=headers, timeout=30)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fabric workspace connectivity smoke test")
    parser.add_argument("--workspace-id", required=True, help="Fabric workspace GUID")
    args = parser.parse_args()

    print("Acquiring token via DefaultAzureCredential ...")
    try:
        token = get_token()
    except Exception as exc:
        print(f"ERROR: could not acquire token: {exc}")
        return 1

    print(f"Calling GET /workspaces/{args.workspace_id}/items ...")
    try:
        response = list_items(args.workspace_id, token)
    except requests.RequestException as exc:
        print(f"ERROR: request failed: {exc}")
        return 1

    if response.status_code == 200:
        data = response.json()
        items = data.get("value", [])
        print(f"HTTP 200 OK — {len(items)} item(s) returned.")
        return 0

    print(f"HTTP {response.status_code} — {response.text[:300]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
