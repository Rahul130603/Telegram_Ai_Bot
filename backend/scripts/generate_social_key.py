from __future__ import annotations

import argparse
from pathlib import Path

from cryptography.fernet import Fernet


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate", action="store_true", help="Print a newly generated key once")
    group.add_argument("--write-env", action="store_true", help="Write a key to empty SOCIAL_TOKEN_KEY without printing")
    group.add_argument("--check", action="store_true", help="Validate configured key without revealing it")
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / ".env"
    text = path.read_text("utf-8") if path.exists() else ""
    line = next((item for item in text.splitlines() if item.startswith("SOCIAL_TOKEN_KEY=")), "")
    existing = line.partition("=")[2].strip()
    if args.check:
        if not existing:
            print("SOCIAL_TOKEN_KEY is missing")
            return 1
        Fernet(existing.encode())
        print("SOCIAL_TOKEN_KEY is valid")
        return 0
    key = Fernet.generate_key().decode()
    if args.generate:
        print(key)
        return 0
    if existing:
        print("Refusing to overwrite existing SOCIAL_TOKEN_KEY")
        return 1
    if "SOCIAL_TOKEN_KEY=" not in text:
        print("SOCIAL_TOKEN_KEY entry missing from .env")
        return 1
    path.write_text(text.replace("SOCIAL_TOKEN_KEY=", f"SOCIAL_TOKEN_KEY={key}", 1), "utf-8")
    print("SOCIAL_TOKEN_KEY written privately to .env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

