from __future__ import annotations

import getpass
import os
from typing import Optional

import keyring
from github import Auth, Github

SERVICE = "crub"
ACCOUNT = "github_pat"
ENV_VAR = "GITHUB_TOKEN"


def _validate_token(token: str) -> None:
    """Raise if token is invalid."""
    g = Github(auth=Auth.Token(token))
    try:
        _ = g.get_user().login  # forces auth check
    finally:
        g.close()


def get_token_interactive() -> str:
    # 1) Environment variable wins (nice for CI)
    env = os.getenv(ENV_VAR)
    if env:
        return env.strip()

    # 2) Keyring
    saved = keyring.get_password(SERVICE, ACCOUNT)
    if saved:
        return saved.strip()

    # 3) Prompt user
    print("No GitHub token found.")
    print("Create one at: https://github.com/settings/tokens")
    print("Scopes: usually 'repo' for private repos; public-only can be 'public_repo'.\n")

    while True:
        token = getpass.getpass("Paste GitHub PAT (input hidden): ").strip()
        if not token:
            print("Token cannot be empty.\n")
            continue

        try:
            _validate_token(token)
        except Exception as e:
            print(f"Token didn't work ({type(e).__name__}). Try again.\n")
            continue

        keyring.set_password(SERVICE, ACCOUNT, token)
        print("Saved token to your system keychain ✅")
        return token


def get_github_client() -> Github:
    token = get_token_interactive()
    return Github(auth=Auth.Token(token))
