"""Connect a Facebook Page to the bot without the OAuth callback flow.

Why this exists: Facebook Login requires the exact callback URL to be
white-listed in the Meta app dashboard, and a quick cloudflared tunnel changes
its hostname on every restart. A Page access token stored in ``.env`` uses the
provider's env fallback path instead (see app/social/factory.py) and needs no
redirect URI at all.

It never prints the tokens you supply or receive.

Usage (from ``backend/``):

    .venv\\Scripts\\python.exe scripts\\set_facebook_token.py --token-file tmp\\fb_user_token.txt
    .venv\\Scripts\\python.exe scripts\\set_facebook_token.py --prompt
    .venv\\Scripts\\python.exe scripts\\set_facebook_token.py --list
    .venv\\Scripts\\python.exe scripts\\set_facebook_token.py --page-id 1234567890
    .venv\\Scripts\\python.exe scripts\\set_facebook_token.py --dry-run

Get the user token from the Graph API Explorer with the ``pages_show_list``,
``pages_read_engagement`` and ``pages_manage_posts`` permissions.
"""

from __future__ import annotations

import argparse
import getpass
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GRAPH = "https://graph.facebook.com/v21.0"
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
REQUIRED_SCOPES = {"pages_show_list", "pages_read_engagement", "pages_manage_posts"}


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw = stripped.split("=", 1)
        values[key.strip()] = raw.strip().strip('"').strip("'")
    return values


def graph(path: str, params: dict[str, str]) -> tuple[int | None, object]:
    url = f"{GRAPH}/{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode())
        except Exception:
            return exc.code, {"error": {"message": "unparseable facebook response"}}
    except Exception as exc:  # noqa: BLE001 - CLI diagnostic
        return None, {"error": {"message": f"{type(exc).__name__}: {exc}"}}


def error_message(body: object) -> str:
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        return str(body["error"].get("message") or "unknown facebook error")
    return "unexpected facebook response shape"


def update_env(path: Path, values: dict[str, str], dry_run: bool) -> Path | None:
    """Replace or append the given keys, preserving every other line."""
    original = path.read_text(encoding="utf-8").splitlines()
    remaining = dict(values)
    output: list[str] = []
    for line in original:
        stripped = line.strip()
        key = stripped.split("=", 1)[0].strip() if "=" in stripped and not stripped.startswith("#") else ""
        if key in remaining:
            output.append(f"{key}={remaining.pop(key)}")
        else:
            output.append(line)
    if output and output[-1].strip():
        output.append("")
    for key, value in remaining.items():
        output.append(f"{key}={value}")
    if dry_run:
        return None
    backup = path.with_name(f"{path.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text("\n".join(output) + "\n", encoding="utf-8")
    return backup


def read_token(args: argparse.Namespace, env: dict[str, str]) -> str:
    if args.token_file:
        return Path(args.token_file).read_text(encoding="utf-8").strip()
    if env.get("FACEBOOK_ACCESS_TOKEN") and args.reuse_env_token:
        return env["FACEBOOK_ACCESS_TOKEN"]
    if args.prompt:
        return getpass.getpass("Paste the Graph API Explorer USER access token (hidden): ").strip()
    print({"error": "no token given; use --token-file <file>, --reuse-env-token, or --prompt"})
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Store a Facebook Page token in .env (no OAuth callback needed)")
    parser.add_argument("--token-file", help="file containing a user access token (keeps it out of the shell history)")
    parser.add_argument("--page-id", help="pick this Page when the account manages several")
    parser.add_argument("--list", action="store_true", help="only list managed Pages, write nothing")
    parser.add_argument("--dry-run", action="store_true", help="show what would change in .env, write nothing")
    parser.add_argument("--reuse-env-token", action="store_true", help="debug an existing FACEBOOK_ACCESS_TOKEN from .env")
    parser.add_argument("--prompt", action="store_true", help="ask for the token interactively (hidden input)")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    app_id, app_secret = env.get("FACEBOOK_APP_ID", ""), env.get("FACEBOOK_APP_SECRET", "")
    if not (app_id and app_secret):
        print({"error": "FACEBOOK_APP_ID / FACEBOOK_APP_SECRET missing in .env"})
        return 2
    print({"env_file": str(ENV_PATH), "app_id_present": True})

    token = read_token(args, env) if not args.list else env.get("FACEBOOK_ACCESS_TOKEN", "")
    if not token and not args.list:
        print({"error": "no token supplied"})
        return 2

    scopes: set[str] = set()
    if not args.list:
        status, body = graph(
            "oauth/access_token",
            {
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": token,
            },
        )
        if isinstance(body, dict) and body.get("access_token"):
            token = str(body["access_token"])
            print({"long_lived_exchange": "ok"})
        else:
            print({"long_lived_exchange": "skipped", "reason": error_message(body)})

        status, body = graph(
            "debug_token",
            {"input_token": token, "access_token": f"{app_id}|{app_secret}"},
        )
        data = body.get("data") if isinstance(body, dict) else None
        if isinstance(data, dict):
            scopes = set(data.get("scopes") or [])
            print({"token_valid": bool(data.get("is_valid")), "token_type": data.get("type")})
            missing = sorted(REQUIRED_SCOPES - scopes)
            if missing:
                print({"warning_missing_scopes": missing})

    status, body = graph("me/accounts", {"fields": "id,name,access_token,category", "access_token": token, "limit": "100"})
    pages = body.get("data") if isinstance(body, dict) else None
    if not isinstance(pages, list):
        print({"error": error_message(body)})
        return 1

    listing = [{"id": page.get("id"), "name": page.get("name"), "category": page.get("category")} for page in pages]
    print({"managed_pages": listing})
    if args.list:
        return 0
    if not pages:
        print({"error": "no managed Pages; the account needs a role on the Page"})
        return 1

    chosen = None
    if args.page_id:
        chosen = next((page for page in pages if str(page.get("id")) == str(args.page_id)), None)
        if not chosen:
            print({"error": f"page {args.page_id} not in the managed list"})
            return 1
    elif len(pages) == 1:
        chosen = pages[0]
    else:
        print({"error": "several Pages found; rerun with --page-id"})
        return 1

    page_token = str(chosen.get("access_token") or token)
    status, body = graph(str(chosen["id"]), {"fields": "id,name", "access_token": page_token})
    if not (isinstance(body, dict) and body.get("id")):
        print({"error": f"page token verification failed: {error_message(body)}"})
        return 1

    page_expiry = "unknown"
    status, body = graph("debug_token", {"input_token": page_token, "access_token": f"{app_id}|{app_secret}"})
    data = body.get("data") if isinstance(body, dict) else None
    if isinstance(data, dict):
        raw_expiry = data.get("expires_at")
        page_expiry = "never" if raw_expiry in (0, None) else time.strftime("%Y-%m-%d", time.localtime(int(raw_expiry)))
        page_scopes = set(data.get("scopes") or [])
        if "pages_manage_posts" not in page_scopes:
            print({"warning": "pages_manage_posts scope missing on the page token"})

    backup = update_env(
        ENV_PATH,
        {"FACEBOOK_PAGE_ID": str(chosen["id"]), "FACEBOOK_ACCESS_TOKEN": page_token},
        args.dry_run,
    )
    print(
        {
            "page": {"id": chosen.get("id"), "name": chosen.get("name")},
            "page_token_expires": page_expiry,
            "env_updated": not args.dry_run,
            "env_backup": str(backup) if backup else None,
            "next": "restart the backend (Ctrl+C then start_server.bat), then send an image and pick Facebook",
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
