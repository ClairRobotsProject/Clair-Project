# AGENTS.md: how to work in this repository

Instructions for anyone changing this repo, and for the AI coding agents they use (Claude Code,
Codex, Copilot, Cursor and so on). Humans: this is also the short version of our version control
rules. We follow **GitFlow** as taught in the course Git lecture. Follow these rules exactly; the
repository enforces most of them (branch ruleset, CI, hooks).

## The branches

| Branch | Purpose | Who writes to it |
| --- | --- | --- |
| `main` | Released versions only. Stays untouched until the team decides to release. | Release and hotfix PRs only |
| `develop` | Integration branch; where all finished work lands. | Pull requests only |
| `feature/<what-you-do>` | New work. Branch from `develop`, merge back into `develop`. | You |
| `bugfix/<bug-name>` | Fix for a reported bug. Branch from `develop`, merge into `develop`. | You |
| `release/<version>` | Prepare a release for testing, e.g. `release/0.2.0`. Branch from `develop`, merge into `main`. | You |
| `hotfix/<bug-title>` | Critical fix for released code. Branch from `main`, merge into `main` **and** `develop`. | You |

Name branches after what they do: `feature/arm-gripper-driver`, not `feature/stuff`. **Never commit
directly to `develop` or `main`**: both are protected and only accept pull requests.

## The workflow, step by step

1. **Know what you are doing.** Every change belongs to a GitHub issue and an easyBacklog story.
   Find or open the issue (`#N`) and note the story ID (`MVP-12`, `CI-1`, `POC-3`, `[B3]`). The
   backlog is easyBacklog, account 57, backlog 438 "Project Sprints" (the team has its address and
   keys; never put an API key in the repo).
2. **Update `develop` and branch from it.**
   ```bash
   git checkout develop && git pull origin develop
   git checkout -b feature/<what-you-do>
   ```
3. **Set up the local checks once** (`pip install -r requirements-dev.txt`, then `pre-commit install`).
   They run flake8, shellcheck, YAML and Python syntax checks, the architecture check and the
   commit-message rule on every commit, and the unit tests before every push. Never bypass them
   (`--no-verify`).
4. **Commit small and often, with a meaningful message that names the issue and the story.**
   ```
   Add the arm Driver and its unit tests

   Refs #81 POC-2
   ```
   Use `Closes #N STORY` on the commit that finishes the issue. Both references are required:
   a GitHub issue `#N` **and** a story ID (`MVP-12`, `CI-1`, `POC-3`, or `[B3]` in brackets).
   The commit-msg hook and CI reject messages without them. Merge commits and `fixup!` commits are exempt.
5. **Pull before you merge.** Before opening the PR (and again if it falls behind):
   ```bash
   git fetch origin && git merge origin/develop     # resolve any conflicts, then commit
   pre-commit run --all-files && (cd clair_agent && python3 -m pytest test)
   ```
   `git merge --abort` cancels a merge that goes wrong. Do not rebase or force-push a branch
   other people have pulled.
6. **Push and open a pull request into `develop`** (into `main` for `release/*` and `hotfix/*`).
   ```bash
   git push -u origin feature/<what-you-do>
   gh pr create --base develop
   ```
   Title says what changed; the body says why and ends with `Closes #N` (or `Refs #N`).
7. **Get it merged.** A PR needs **one approval from a teammate** and the three CI checks green:
   *Lint, syntax and architecture checks*, *Unit tests (no ROS needed)* and
   *Build clair_agent on ROS 2 Humble*. Do not merge your own PR without a review. If the checks
   or review are red, fix the branch with new commits.
8. **Clean up.** After the merge: `git checkout develop && git pull origin develop`, delete your local
   branch (`git branch -d <branch>`), and update the story status in the backlog.

## Releasing (when the team decides)

Create `release/<version>` from `develop`, bump `<version>` in `clair_agent/package.xml`, test, and
open a PR into `main`. Merging into `main` runs CD: it repeats every CI check and publishes a
GitHub Release with a source archive. If that version already exists, nothing is published and the
run shows a warning, so always bump the version. Merging into `main` also closes the issues
that commits reference with `Closes #N`. A `hotfix/*` branch starts from `main`, merges into `main`
and then into `develop`.

## What CI and the hooks check

- `pre-commit run --all-files` is exactly what the CI lint job runs; green locally means green there.
- `scripts/check_architecture.py`: `core/`, `actions/`, `policies/` and `skills/` must not import
  ROS or Gazebo code; only a Driver (or the node wiring) may touch `cmd_vel`.
- `scripts/check_commit_message.py`: the issue and story reference rule above.
- Unit tests: `cd clair_agent && python3 -m pytest test` (no ROS needed).
- `LICENSE` is excluded from all hooks on purpose; never edit it.

## Rules for AI agents

- **Ask the human before anything outward-facing:** `git push`, opening or merging a PR, creating or
  closing issues, changing backlog stories, deleting remote branches. Local work (branches, commits,
  running the checks) you may do freely.
- **Never** push to `develop` or `main`, force-push a shared branch, rewrite published history, skip
  hooks (`--no-verify`) or edit another teammate's branch. A force-push to your own unreviewed feature
  branch is the only exception, uses `--force-with-lease`, and needs the human's explicit approval.
- Use the human's own git identity as already configured; do not change git config.
- Never commit secrets: API keys, tokens, passwords, `.env` files. Keep them out of the repo and
  out of commit messages.
- Make the smallest change that does the job, in the branch for that job. Do not mix unrelated
  fixes into one branch; open a separate issue and branch instead.
- Do not edit other people's backlog stories or issues. Add what is missing; ask before changing
  what exists.

## Quick reference

```bash
git checkout develop && git pull origin develop      # start from the latest develop
git checkout -b feature/<name>                       # new branch
git add <files> && git commit                        # message: "...\n\nRefs #N STORY"
git fetch origin && git merge origin/develop         # before the PR
pre-commit run --all-files                           # same checks as CI
git push -u origin feature/<name> && gh pr create --base develop
```

| Problem | Fix |
| --- | --- |
| Commit rejected: "missing a GitHub issue ... and a story ID" | Add `Refs #N STORY` to the message and commit again. |
| A hook changed files | Review `git diff`, `git add` the fixes, commit again. |
| PR says branch is behind or has conflicts | `git fetch origin && git merge origin/develop`, resolve, push. |
| CI check red | Open the run on the PR's Checks tab, fix, push a new commit. |
| Committed on `develop` by mistake | Do not push. `git branch feature/<name>` then `git reset --hard origin/develop`, and continue on the new branch. |
