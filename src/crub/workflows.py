from __future__ import annotations

import os
import re
import shlex
import subprocess
from importlib import resources
from typing import Optional

import keyring
from github import GithubException

from crub.auth import get_github_client

def _run_git(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        capture_output=True,
    )

def _git_stdout(args: list[str]) -> str:
    return _run_git(args).stdout.strip()

def _ensure_git_repo() -> None:
    try:
        inside = _git_stdout(["rev-parse", "--is-inside-work-tree"])
    except subprocess.CalledProcessError:
        raise RuntimeError("Not inside a git repository.")
    if inside != "true":
        raise RuntimeError("Not inside a git repository.")

def _local_branch_exists(branch: str) -> bool:
    cp = _run_git(["show-ref", "--verify", f"refs/heads/{branch}"], check=False)
    return cp.returncode == 0

def _remote_branch_exists(branch: str) -> bool:
    cp = _run_git(["ls-remote", "--heads", "origin", branch], check=False)
    return cp.returncode == 0 and bool(cp.stdout.strip())

def _checkout_existing_branch(branch: str) -> None:
    if _local_branch_exists(branch):
        _run_git(["checkout", branch])
        return
    if _remote_branch_exists(branch):
        _run_git(["checkout", "-t", f"origin/{branch}"])
        return
    raise RuntimeError(f"Branch '{branch}' not found locally or on origin.")

def _current_branch() -> str:
    branch = _git_stdout(["branch", "--show-current"])
    if not branch:
        raise RuntimeError("Could not determine current branch.")
    return branch

def _origin_repo_slug() -> str:
    url = _git_stdout(["config", "--get", "remote.origin.url"])
    if not url:
        raise RuntimeError("Missing remote.origin.url.")

    patterns = [
        r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$",
        r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$",
        r"^ssh://git@github\.com/(?P<owner>[^/]+)/(?P<repo>.+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            owner = match.group("owner")
            repo = match.group("repo")
            return f"{owner}/{repo}"
    raise RuntimeError(f"Unsupported GitHub remote URL format: {url}")

def _push_branch(branch: str) -> None:
    cp = _run_git(["push", "-u", "origin", branch], check=False)
    if cp.returncode == 0:
        return
    _run_git(["push", "origin", branch], check=True)

def _delete_local_branch_if_exists(branch: str) -> bool:
    if not _local_branch_exists(branch):
        return False
    _run_git(["branch", "-D", branch])
    return True

def _delete_remote_branch_if_exists(branch: str) -> bool:
    if not _remote_branch_exists(branch):
        return False
    _run_git(["push", "origin", "--delete", branch])
    return True

def _has_staged_changes() -> bool:
    cp = _run_git(["diff", "--cached", "--quiet"], check=False)
    return cp.returncode == 1

def _commit_all_if_changed(message: str) -> bool:
    _run_git(["add", "-A"])
    if not _has_staged_changes():
        return False
    _run_git(["commit", "-m", message])
    return True

def _run_ai(instruction: str) -> None:
    template = os.getenv("CRUB_AI_COMMAND")
    if not template:
        raise RuntimeError(
            "Set CRUB_AI_COMMAND to your AI CLI. Example: "
            "CRUB_AI_COMMAND='codex {instruction}'"
        )

    tokens = shlex.split(template)
    argv: list[str] = []
    replaced = False
    for token in tokens:
        if token == "{instruction}":
            argv.append(instruction)
            replaced = True
        else:
            argv.append(token)
    if not replaced:
        argv.append(instruction)

    subprocess.run(argv, check=True)

def _default_base_branch(repo) -> str:
    if getattr(repo, "default_branch", None):
        return repo.default_branch
    if _local_branch_exists("main"):
        return "main"
    if _local_branch_exists("master"):
        return "master"
    return "main"

def _collect_pr_feedback(pr) -> list[str]:
    feedback: list[str] = []
    for c in pr.get_review_comments():
        feedback.append(f"[review_comment] {c.user.login}: {c.body}")
    for c in pr.get_issue_comments():
        feedback.append(f"[issue_comment] {c.user.login}: {c.body}")
    return feedback

def _resolve_pr(repo, branch: str, pr_number: Optional[int]):
    if pr_number is not None:
        return repo.get_pull(pr_number)
    owner = repo.owner.login
    head_ref = f"{owner}:{branch}"
    prs = list(repo.get_pulls(state="open", head=head_ref))
    if not prs:
        raise RuntimeError(f"No open PR found for branch '{branch}'.")
    if len(prs) > 1:
        raise RuntimeError("Multiple open PRs found. Specify one with --pr <number>.")
    return prs[0]

def clear_auth_token() -> None:
    keyring.delete_password("crub", "github_pat")
    print("Token removed.")

def create_branch(branch: str) -> None:
    _ensure_git_repo()
    if _local_branch_exists(branch) or _remote_branch_exists(branch):
        raise RuntimeError(f"Branch '{branch}' already exists.")
    _run_git(["checkout", "-b", branch])
    print(f"Created and switched to branch '{branch}'.")

def submit_pr(branch: Optional[str], base: Optional[str]) -> None:
    _ensure_git_repo()
    selected_branch = branch or _current_branch()
    _checkout_existing_branch(selected_branch)
    _push_branch(selected_branch)

    g = get_github_client()
    try:
        slug = _origin_repo_slug()
        repo = g.get_repo(slug)
        owner = repo.owner.login
        target_base = base or _default_base_branch(repo)
        head_ref = f"{owner}:{selected_branch}"

        title = _git_stdout(["log", "-1", "--pretty=%s"])
        if not title:
            title = f"PR for {selected_branch}"

        try:
            pr = repo.create_pull(
                title=title,
                body=f"Automated PR from `{selected_branch}`.",
                head=head_ref,
                base=target_base,
            )
        except GithubException as exc:
            existing = list(repo.get_pulls(state="open", head=head_ref, base=target_base))
            if not existing:
                raise RuntimeError(f"Failed to create PR: {exc.data}") from exc
            pr = existing[0]

        print(f"PR #{pr.number}: {pr.html_url}")
    finally:
        g.close()

def revise_branch(branch: str, instruction: str) -> None:
    _ensure_git_repo()
    _checkout_existing_branch(branch)
    _run_ai(instruction)
    changed = _commit_all_if_changed(f"revise: {instruction[:72]}")
    if not changed:
        print("No changes detected after AI revise.")
        return
    _push_branch(branch)
    print(f"Revised '{branch}', committed, and pushed.")

def review_branch(branch: Optional[str], pr_number: Optional[int], comment: bool) -> None:
    _ensure_git_repo()
    selected_branch = branch or _current_branch()
    _checkout_existing_branch(selected_branch)

    g = get_github_client()
    try:
        repo = g.get_repo(_origin_repo_slug())
        pr = _resolve_pr(repo, selected_branch, pr_number)
        feedback = _collect_pr_feedback(pr)
        if not feedback:
            print(f"No PR comments to address for PR #{pr.number}.")
            return

        instruction = (
            f"Address all feedback for GitHub PR #{pr.number} ({pr.title}).\n"
            "Make the required code changes in this repository.\n"
            "Feedback:\n- "
            + "\n- ".join(feedback)
        )
        _run_ai(instruction)

        changed = _commit_all_if_changed(f"review: address PR #{pr.number} comments")
        if not changed:
            print("No changes detected after AI review.")
            return

        _push_branch(selected_branch)
        if comment:
            pr.create_issue_comment("Addressed review feedback in latest commit(s).")
        print(f"Addressed PR #{pr.number} comments, committed, and pushed.")
    finally:
        g.close()

def wrap_branch(branch: Optional[str], pr_number: Optional[int]) -> None:
    _ensure_git_repo()
    selected_branch = branch or _current_branch()

    g = get_github_client()
    try:
        repo = g.get_repo(_origin_repo_slug())
        pr = _resolve_pr(repo, selected_branch, pr_number)
        if not pr.merged:
            raise RuntimeError(
                f"PR #{pr.number} is not merged yet (state={pr.state})."
            )

        base_branch = pr.base.ref
        if selected_branch == base_branch:
            raise RuntimeError("Refusing to delete base branch.")

        _checkout_existing_branch(base_branch)
        local_deleted = _delete_local_branch_if_exists(selected_branch)
        remote_deleted = _delete_remote_branch_if_exists(selected_branch)

        print(
            f"PR #{pr.number} is merged. Cleanup complete for '{selected_branch}'. "
            f"local_deleted={local_deleted}, remote_deleted={remote_deleted}"
        )
    finally:
        g.close()


def status_branch(branch: Optional[str] = None) -> None:
    _ensure_git_repo()
    selected_branch = branch or _current_branch()
    print(f"Branch: {selected_branch}")

    g = get_github_client()
    try:
        repo = g.get_repo(_origin_repo_slug())
        owner = repo.owner.login
        head_ref = f"{owner}:{selected_branch}"

        open_prs = list(repo.get_pulls(state="open", head=head_ref))
        closed_prs = list(repo.get_pulls(state="closed", head=head_ref))
        prs = open_prs + closed_prs

        if not prs:
            print("PR: none")
            return

        if len(prs) == 1:
            pr = prs[0]
            state = "merged" if pr.merged else pr.state
            print(f"PR: #{pr.number} ({state}) {pr.html_url}")
            return

        print(f"PRs: {len(prs)} associated")
        for pr in prs:
            state = "merged" if pr.merged else pr.state
            print(f"- #{pr.number} ({state}) {pr.html_url}")
    finally:
        g.close()


def print_instructions() -> None:
    try:
        guide_text = resources.files("crub").joinpath("AGENT_GUIDE.md").read_text(
            encoding="utf-8"
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Bundled AGENT_GUIDE.md is missing from this installation.") from exc
    print(guide_text)
