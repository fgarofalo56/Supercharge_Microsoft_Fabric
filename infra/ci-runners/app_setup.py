"""Loopback GitHub App registration with direct Key Vault storage."""

import argparse
import html
import json
import re
import secrets
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Protocol
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from register_app import manifest, valid_callback


class SecretStore(Protocol):
    """Minimal vault interface for registration."""

    def set_secret(self, name: str, value: str) -> object:
        """Persist a secret without logging its value."""
        ...


def serve(client: SecretStore, port: int) -> None:
    """Run a single registration session on the loopback interface."""
    state = secrets.token_urlsafe(32)
    base = f"http://127.0.0.1:{port}"
    pending: dict = {}
    finished = False

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            """Suppress callback codes and request paths."""
            return None

        def respond(self, status: int, body: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; form-action https://github.com; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(body.encode())

        def do_GET(self) -> None:
            nonlocal finished
            if self.headers.get("Host") != f"127.0.0.1:{port}":
                self.respond(403, "Invalid host")
                return
            parsed = urlsplit(self.path)
            if parsed.path == "/" and parsed.query == f"session={state}":
                payload = html.escape(json.dumps(manifest(base)), quote=True)
                self.respond(
                    200,
                    f'<form method="post" action="https://github.com/settings/apps/new?state={state}">'
                    f'<input type="hidden" name="manifest" value="{payload}">'
                    "<button>Create runner App on GitHub</button></form>",
                )
                return
            if parsed.path != "/callback" or finished:
                self.respond(404, "Not found")
                return
            try:
                code = valid_callback(parsed.query, state)
            except (ValueError, TypeError):
                self.respond(403, "Invalid callback")
                return
            try:
                if not pending:
                    request = Request(
                        f"https://api.github.com/app-manifests/{code}/conversions",
                        data=b"{}",
                        headers={
                            "Accept": "application/vnd.github+json",
                            "Content-Type": "application/json",
                            "User-Agent": "fabric-runner-setup",
                        },
                        method="POST",
                    )
                    with urlopen(request, timeout=30) as response:
                        pending.update(json.load(response))
                app_id = int(pending["id"])
                slug = pending["slug"]
                if not re.fullmatch(r"[A-Za-z0-9-]+", slug):
                    raise ValueError("Invalid App slug")
                client.set_secret("github-app-private-key", pending["pem"])
                client.set_secret("github-app-id", str(app_id))
                pending.clear()
                finished = True
                self.respond(
                    200,
                    f"<p>App ID: {app_id}. Key stored in Key Vault.</p>"
                    f'<a href="https://github.com/apps/{slug}/installations/new">Install App</a>'
                    "<p>Select only Supercharge_Microsoft_Fabric.</p>",
                )
                print(
                    f"App ID: {app_id}. Complete repository installation in your browser."
                )
            except Exception:
                self.respond(
                    502,
                    "Setup failed; secret details suppressed. Refresh to retry storage "
                    "while this process remains open. If you stop it, revoke the App key in GitHub.",
                )

    with HTTPServer(("127.0.0.1", port), Handler) as server:
        server.timeout = 1
        print(f"Open {base}/?session={state}", flush=True)
        deadline = time.monotonic() + 3600
        while not finished and time.monotonic() < deadline:
            server.handle_request()
    if not finished:
        raise SystemExit("Setup expired. Revoke any unstored App key before retrying.")


def main() -> None:
    """Check vault access before starting browser registration."""
    from azure.identity import AzureCliCredential
    from azure.keyvault.secrets import SecretClient

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-name", required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{1,22}[A-Za-z0-9]", args.vault_name):
        parser.error("Invalid vault name")
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535")
    with (
        AzureCliCredential() as credential,
        SecretClient(
            vault_url=f"https://{args.vault_name}.vault.azure.net",
            credential=credential,
        ) as client,
    ):
        client.set_secret("github-app-setup-probe", "registration-preflight")
        serve(client, args.port)


if __name__ == "__main__":
    main()
