import argparse
import subprocess

from crub.workflows import (
    clear_auth_token,
    create_branch,
    review_branch,
    revise_branch,
    status_branch,
    submit_pr,
    wrap_branch,
)


def _build_parser() -> tuple[argparse.ArgumentParser, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(
        prog="crub",
        description="Agent-first GitHub workflow CLI.",
        epilog=(
            "Workflow:\n"
            "  1) Start a coding session: crub create <branch>\n"
            "  2) Ask the agent to implement work: crub revise <branch> \"<instruction>\"\n"
            "  3) Submit for review: crub submit [branch] [--base main]\n"
            "  4) Address PR comments: crub review [branch] [--pr <number>]\n"
            "  5) Final cleanup after merge: crub wrap [branch] [--pr <number>]\n"
            "\n"
            "Use `crub status` anytime to see branch and linked PRs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    auth_parser = subparsers.add_parser("auth", help="Authentication utilities")
    auth_sub = auth_parser.add_subparsers(dest="auth_cmd")
    auth_sub.add_parser("clear", help="Clear stored GitHub token")

    create_parser = subparsers.add_parser(
        "create",
        help="Start a coding session on a new branch",
    )
    create_parser.add_argument("branch_name")

    submit_parser = subparsers.add_parser(
        "submit",
        help="Open a PR for the current or specified branch",
    )
    submit_parser.add_argument("branch_name", nargs="?")
    submit_parser.add_argument("--base", dest="base_branch")

    revise_parser = subparsers.add_parser(
        "revise",
        help="Apply instruction-driven changes via your AI command",
    )
    revise_parser.add_argument("branch_name")
    revise_parser.add_argument("instruction")

    review_parser = subparsers.add_parser(
        "review",
        help="Pull PR feedback and have AI address comments",
    )
    review_parser.add_argument("branch_name", nargs="?")
    review_parser.add_argument("--pr", dest="pr_number", type=int)
    review_parser.add_argument(
        "--comment",
        action="store_true",
        help="Comment on the PR after pushing updates",
    )

    wrap_parser = subparsers.add_parser(
        "wrap",
        help="After merge, clean up feature branches",
    )
    wrap_parser.add_argument("branch_name", nargs="?")
    wrap_parser.add_argument("--pr", dest="pr_number", type=int)

    status_parser = subparsers.add_parser(
        "status",
        help="Show branch context and associated PRs",
    )
    status_parser.add_argument("branch_name", nargs="?")

    return parser, auth_parser


def main() -> int:
    parser, auth_parser = _build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0
    if args.command == "auth" and not getattr(args, "auth_cmd", None):
        auth_parser.print_help()
        return 0

    try:
        if args.command == "auth" and args.auth_cmd == "clear":
            clear_auth_token()
        elif args.command == "create":
            create_branch(args.branch_name)
        elif args.command == "submit":
            submit_pr(args.branch_name, args.base_branch)
        elif args.command == "revise":
            revise_branch(args.branch_name, args.instruction)
        elif args.command == "review":
            review_branch(args.branch_name, args.pr_number, args.comment)
        elif args.command == "wrap":
            wrap_branch(args.branch_name, args.pr_number)
        elif args.command == "status":
            status_branch(args.branch_name)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        err = str(exc).strip() or type(exc).__name__
        print(f"Error: {err}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
