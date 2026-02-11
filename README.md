# crub

**crub** (Code Review User Experience) is a CLI tool that streamlines AI-assisted development with proper code review workflows. It enforces a PR-based review process for AI-generated code, ensuring changes go through proper review before merging.

## What It Does

crub manages the full lifecycle of AI-assisted feature development:

1. **Instruct** the agent with project-specific guidance
2. **Create** a feature branch
3. **Work** on it using AI coding tools (or manually)
4. **Submit** changes as a GitHub PR
5. **Review** and address PR feedback automatically with AI
6. **Wrap up** by cleaning branches after merge

## Why Use crub?

- **Enforces code review**: AI-generated code goes through PRs, not directly to main
- **Tool agnostic**: Works with any AI coding tool (Claude Code, Cursor, Copilot, etc.)
- **Automates PR feedback**: AI can automatically address review comments
- **Simple workflow**: Familiar git-style commands

## Installation

```bash
pip install crub
```

Or install from source:

```bash
git clone https://github.com/alexanderkyoo/crub.git
cd crub
pip install -e .
```

## Setup

### 1. GitHub Authentication

crub needs a GitHub Personal Access Token (PAT) to create and manage PRs.

**Create a token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with:
   - `repo` (for private repos)
   - `public_repo` is enough for public-only workflows

**Configure crub:**
- No explicit login command is required.
- On first GitHub action (`submit`, `review`, `wrap`, `status`), crub prompts for a token and stores it in your keyring.
- To clear a saved token: `crub auth clear`

### 2. Configure Your AI Tool

crub works with any AI coding CLI tool. Set the `CRUB_AI_COMMAND` environment variable to your preferred tool:

```bash
# For Claude Code
export CRUB_AI_COMMAND="claude-code {instruction}"

# For Cursor CLI (if available)
export CRUB_AI_COMMAND="cursor --ai {instruction}"

# For a custom wrapper script
export CRUB_AI_COMMAND="my-ai-wrapper {instruction}"
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

If `{instruction}` is present, crub replaces it with your instruction text.
If `{instruction}` is omitted, crub appends the instruction as the last argument.

## Usage

### Basic Workflow

```bash
# 1. Print project guidance for the agent
crub instruct

# 2. Create a new feature branch
crub create auth-feature

# 3. Do your work (use your AI tool directly, or work manually)
# Your AI tool makes changes, you review them locally

# 4. Submit a PR when ready
crub submit

# 5. Address review comments automatically
crub review
```

### Commands

#### `crub`

Shows the guided workflow help screen.

#### `crub instruct`

Prints `AGENT_GUIDE.md` from the current repository root.

```bash
crub instruct
```

#### `crub create <branch-name>`

Creates a new branch and switches to it.

```bash
crub create user-authentication
```

#### `crub submit [branch-name] [--base <target-branch>]`

Creates a GitHub PR from your branch.

```bash
# Submit current branch to main (default)
crub submit

# Submit specific branch
crub submit auth-feature

# Submit to a different base branch
crub submit auth-feature --base develop
```

The PR title defaults to your latest commit message. The branch is automatically pushed to GitHub.

#### `crub revise <branch-name> "<instruction>"`

Manually instruct the AI to make changes.

```bash
crub revise auth-feature "convert all variable names to camelCase"
crub revise auth-feature "add error handling to the login function"
```

Changes are automatically committed and pushed.

#### `crub review [branch-name] [--pr <number>] [--comment]`

Automatically addresses PR review comments using AI.

```bash
# Review current branch's PR
crub review

# Review specific branch
crub review auth-feature

# If multiple PRs exist for the branch
crub review auth-feature --pr 123

# Add a comment on the PR after pushing changes
crub review --comment
```

The AI fetches all PR comments, makes the requested changes, commits, and pushes.

#### `crub status [branch-name]`

Shows current (or specified) branch and associated PR(s).

```bash
# Status for current branch
crub status

# Status for a specific branch
crub status auth-feature
```

#### `crub wrap [branch-name] [--pr <number>]`

Cleans up branches after a PR is merged.

```bash
# Wrap up current branch
crub wrap

# Wrap up specific branch
crub wrap auth-feature
```

This command:
- Verifies the PR is actually merged
- Switches to the base branch
- Deletes local and remote branches
- Keeps you on the base branch

#### `crub auth clear`

Removes your stored GitHub token.

```bash
crub auth clear
```

## Advanced Usage

### Working with Stacked PRs

If you're working on a feature that builds on another unmerged feature:

```bash
# Create base feature
crub create feature-1
# ... work on it ...
crub submit

# Create dependent feature
crub create feature-2
# ... work on it ...

# Submit as a stacked PR (targets feature-1, not main)
crub submit --base feature-1
```

### Using Different AI Tools

You can switch AI tools by changing the `CRUB_AI_COMMAND` environment variable:

```bash
# Try a different tool for this session
CRUB_AI_COMMAND="aider {instruction}" crub revise my-branch "refactor for clarity"
```

### Multiple PRs for One Branch

If you have multiple PRs from the same branch (e.g., to different base branches):

```bash
# crub will error and ask you to specify which PR
crub review my-branch --pr 123
```

## Configuration

### Environment Variables

- `CRUB_AI_COMMAND`: Your AI CLI command (required for `revise` and `review`)
  - `{instruction}` placeholder is optional
  - Example: `"claude-code {instruction}"`

### GitHub Token Storage

Tokens are stored securely using your system's keyring:
- macOS: Keychain
- Linux: Secret Service API / KWallet
- Windows: Windows Credential Locker

## Examples

### Example 1: Simple Feature Development

```bash
# Start new feature
crub create user-profile

# Use your AI tool directly to build the feature
claude-code "implement user profile page with avatar upload"

# Submit for review
crub submit

# Teammate leaves comments asking for changes
# Address them automatically
crub review --comment

# After PR is merged
crub wrap
```

### Example 2: Quick Fix with AI Revision

```bash
# Create fix branch
crub create fix-typos

# Make a quick change with AI
crub revise fix-typos "fix all typos in README.md"

# Submit
crub submit
```

### Example 3: Complex Multi-Step Feature

```bash
# Start feature
crub create payment-integration

# Work iteratively with AI
crub revise payment-integration "add Stripe SDK and basic setup"
crub revise payment-integration "implement checkout flow"
crub revise payment-integration "add error handling and logging"

# Submit for review
crub submit

# Address review feedback
crub review --comment

# After merge
crub wrap
```

## Requirements

- Python 3.10+
- Git
- GitHub account with repository access
- An AI coding tool (Claude Code, Cursor, etc.) - optional but recommended

## Troubleshooting

**"Not inside a git repository"**
- Make sure you're in a git repository directory
- Run `git init` if starting a new project

**"Missing remote.origin.url"**
- Your git repo needs a GitHub remote
- Add one: `git remote add origin git@github.com:username/repo.git`

**"Set CRUB_AI_COMMAND to your AI CLI"**
- You need to configure which AI tool to use
- Set the environment variable: `export CRUB_AI_COMMAND="your-tool {instruction}"`

**"No open PR found for branch"**
- You need to create a PR first with `crub submit`
- Or the PR might be closed/merged already

**Authentication errors**
- Run `crub auth clear` to remove the cached token
- Re-run any GitHub command (`crub submit`, `crub status`, etc.) to enter a new token
- Make sure your token has `repo` permissions

## Contributing

Issues and pull requests welcome! This tool is designed to be simple and focused.

## License

MIT
