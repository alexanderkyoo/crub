# Agent Steering Guide for crub

This document explains how AI coding agents should use crub to maintain proper code review workflows.

## Core Principle

**AI agents should NEVER directly modify code on main/master branches.** All changes must go through crub's PR-based review process.

## Agent Workflow

### 1. Starting Work on a Task

When a user asks you to implement a feature or fix:

```bash
# Create a new branch for this work
crub create <descriptive-branch-name>
```

**Branch naming conventions:**
- Features: `feature-user-auth`, `add-payment-integration`
- Fixes: `fix-login-bug`, `fix-memory-leak`
- Refactors: `refactor-api-layer`, `cleanup-unused-code`

### 2. Making Changes

Make your code changes normally. You can:
- Edit files directly
- Run tests
- Iterate on the implementation

**DO NOT** commit or push manually. crub handles this.

### 3. Submitting for Review

Once changes are complete and tested:

```bash
# Submit current branch as a PR
crub submit
```

**What crub does:**
- Commits all changes
- Pushes to GitHub
- Creates a PR with an appropriate title
- Returns the PR URL

**Tell the user:**
- The PR URL
- What you implemented
- What they should review

### 4. Addressing Review Feedback

When the user says "address the review comments" or similar:

```bash
# Automatically fetch and address all PR comments
crub review --comment
```

**What crub does:**
- Fetches all review comments from GitHub
- Provides them to you as instructions
- You make the necessary changes
- crub commits and pushes
- Optionally comments on the PR that changes were made

### 5. Manual Revisions

If the user asks for specific changes after seeing the PR:

```bash
crub revise <branch-name> "<user's instruction>"
```

**Example:**
```bash
crub revise feature-auth "add input validation to the login form"
```

### 6. After PR is Merged

Once the user confirms the PR is merged:

```bash
# Clean up branches
crub wrap
```

**What crub does:**
- Verifies PR is merged
- Switches to base branch
- Deletes local and remote feature branches

## Decision Trees

### When User Asks to "Implement Feature X"

```
1. Is there already a crub branch for this?
   NO  → crub create feature-x
   YES → git checkout feature-x (or crub will handle this)

2. Implement the feature
   - Make code changes
   - Test locally

3. crub submit

4. Tell user: "I've created PR #123 at [URL]. Please review the changes."
```

### When User Says "Fix the Issues in the PR"

```
1. Is this about review comments?
   YES → crub review --comment
   NO  → Ask for clarification

2. Tell user: "I've addressed the feedback and pushed updates."
```

### When User Gives Specific Revision Instruction

```
1. crub revise <branch> "<instruction>"

2. Tell user: "Changes made and pushed to PR."
```

## Common Scenarios

### Scenario 1: New Feature Request

**User:** "Add user authentication to the app"

**Agent:**
```bash
crub create feature-user-auth
# [make changes]
crub submit
```

**Response:** "I've implemented user authentication with login/logout functionality. Created PR #45: [URL]. Please review the changes, particularly the password hashing implementation."

### Scenario 2: Review Feedback

**User:** "Address the comments on the PR"

**Agent:**
```bash
crub review --comment
```

**Response:** "I've addressed all 3 review comments: added error handling, fixed the typo, and updated the tests. Changes are pushed."

### Scenario 3: Quick Fix After PR

**User:** "Can you make the button blue instead of red?"

**Agent:**
```bash
crub revise feature-ui-updates "change button color from red to blue"
```

**Response:** "Updated the button color to blue and pushed to the PR."

### Scenario 4: Stacked Changes

**User:** "Build a dashboard that uses the new API we're working on"

**Agent:**
```bash
crub create feature-dashboard --base feature-new-api
# [make changes]
crub submit --base feature-new-api
```

**Response:** "Created PR #47 for the dashboard. Note: this PR targets the `feature-new-api` branch and should be merged after that PR is complete."

### Scenario 5: Post-Merge Cleanup

**User:** "The PR was merged"

**Agent:**
```bash
crub wrap
```

**Response:** "Cleaned up the feature branch. You're now on main with the latest changes."

## Error Handling

### "Not inside a git repository"

**Agent response:** "This directory isn't a git repository. Should I initialize one with `git init` and set up a GitHub remote?"

### "Branch already exists"

**Agent response:** "A branch with this name already exists. Should I:
1. Switch to the existing branch and continue work?
2. Choose a different branch name?"

### "No open PR found"

**Agent response:** "There's no open PR for this branch yet. Should I create one with `crub submit`?"

### "Multiple PRs found"

**Agent response:** "This branch has multiple open PRs:
- PR #123 → main
- PR #124 → develop

Which one should I work with? Use `crub review --pr <number>` to specify."

### "Set CRUB_AI_COMMAND"

**Agent response:** "The `CRUB_AI_COMMAND` environment variable isn't set. This tells crub which AI tool to use. Would you like me to help set this up?"

## Best Practices

### DO:
- ✅ Always create a new branch for each feature/fix
- ✅ Use descriptive branch names
- ✅ Submit PRs as soon as work is complete
- ✅ Address all review feedback before asking for re-review
- ✅ Clean up branches after merge
- ✅ Provide context to the user about what you did

### DON'T:
- ❌ Commit directly to main/master
- ❌ Push without using crub
- ❌ Create multiple branches for the same feature
- ❌ Ignore PR review comments
- ❌ Delete branches manually (use `crub wrap`)

## Integration Notes

### With Other Tools

crub is designed to work alongside your normal development tools:
- **Testing**: Run tests before `crub submit`
- **Linting**: Run linters/formatters before `crub submit`
- **Other AI tools**: Use them for implementation, use crub for workflow

### With CI/CD

After `crub submit`, normal CI/CD pipelines will run:
- Tests will run automatically
- Deployment previews may be created
- Wait for CI to pass before asking for review

### With Team Workflows

Respect team conventions:
- Use team's branch naming patterns
- Follow team's PR description templates
- Tag appropriate reviewers
- Link to relevant issues

## Command Reference

Quick reference for the agent:

| Command | Use When | Example |
|---------|----------|---------|
| `crub create <branch>` | Starting new work | `crub create fix-login-bug` |
| `crub submit` | Work is ready for review | `crub submit` |
| `crub submit --base <branch>` | Creating stacked PR | `crub submit --base feature-api` |
| `crub revise <branch> "<instruction>"` | User wants specific change | `crub revise fix-bug "add logging"` |
| `crub review` | Addressing PR comments | `crub review --comment` |
| `crub review --pr <number>` | Multiple PRs exist | `crub review --pr 123` |
| `crub status` | Checking PR status | `crub status` |
| `crub wrap` | After PR is merged | `crub wrap` |

## Philosophy

crub exists to enforce discipline in AI-assisted development:

1. **Code review is non-negotiable**: Even AI-generated code needs human review
2. **Transparency**: All changes go through PRs with clear diffs
3. **Traceability**: Every change has a PR number and discussion
4. **Collaboration**: PRs enable team feedback and learning
5. **Safety**: Review catches issues before they reach production

As an AI agent, your job is to:
- **Generate good code** (that's the easy part)
- **Follow the workflow** (that's what crub enforces)
- **Communicate clearly** (tell users what you did and why)
- **Respect the process** (no shortcuts around review)

## Troubleshooting for Agents

### User Wants to Skip Review

**User:** "Just merge it directly"

**Agent response:** "crub enforces a PR-based workflow for safety. I've created PR #X - you can approve and merge it yourself if you're confident in the changes. If you want to bypass crub entirely, you'd need to use git directly, but I'd recommend keeping the review process."

### User Is Confused About Workflow

**Agent:** "Let me explain the crub workflow:
1. I create a branch and make changes
2. I submit a PR for you to review
3. You can either merge it or leave feedback
4. I can automatically address feedback with `crub review`
5. After merge, we clean up with `crub wrap`

This ensures nothing goes to production without review."

### Complex Multi-Step Tasks

For large features, break into multiple PRs:

**User:** "Build a complete authentication system"

**Agent:**
```bash
# PR 1: Basic structure
crub create feature-auth-structure
# [implement models and database]
crub submit

# PR 2: Login/logout
crub create feature-auth-login
# [implement login flow]
crub submit

# PR 3: Password reset
crub create feature-auth-reset
# [implement reset flow]
crub submit
```

Small, focused PRs are easier to review.

---

**Remember:** crub is a tool that helps AI agents follow human best practices. Use it consistently, explain what you're doing, and maintain the discipline of code review.