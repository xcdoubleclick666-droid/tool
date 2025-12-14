# Copilot instructions for this repository

Repository status
- This repository currently has no README or detectable source files (no `package.json`, `pyproject.toml`, `go.mod`, or similar) at the workspace root. If you see different files locally, point me to their paths.

Primary goal for AI agents
- Make minimal, reversible changes. Ask before changing project layout or removing files.

How to get started (concrete steps)
- Look for these files in the repo root (in order): `package.json`, `pyproject.toml`, `requirements.txt`, `setup.py`, `go.mod`, `Cargo.toml`, `README.md`, `src/`, `cmd/`, `app/`.
- If you find `package.json`: run `npm ci` then `npm test` to discover scripts.
- If you find Python config (pyproject/setup/requirements): create a venv and run `pip install -r requirements.txt` or `pip install -e .` then `pytest`.
- If you find `go.mod`: run `go test ./...`.
- If you find `Cargo.toml`: run `cargo test`.

Codebase exploration priorities
- Identify the program entrypoint (examples: `src/main.py`, `cmd/server/main.go`, `src/index.ts`).
- Find tests (folders named `tests`, `test`, or files matching `*_test.go`, `test_*.py`, `*.spec.ts`). Run them early to understand behavior.
- Search for configuration files (`.env`, `.env.example`, `config/*.yaml`), CI workflows (`.github/workflows`), and Dockerfiles.

Project-specific patterns to look for
- If you encounter `src/` with many small files, prefer making a small, well-scoped change and adding tests.
- If there is a mono-repo style layout (top-level packages or `packages/` folder), modify only the package that contains failing tests or the requested feature.

Merging guidance for this file
- If an existing `.github/copilot-instructions.md` is present, preserve any project-specific commands and examples. Add missing quick-start commands and a short note about repo emptiness if applicable.

When uncertain
- Ask the repository owner for the preferred language, build commands, and any secret/environment setup before running destructive commands.

Quick checklist for PRs from AI agents
- Include: short description, files changed rationale, how you tested (commands), and any manual steps for reviewers.

Contact/Follow-up
- If this repo should contain code (not empty), reply with the top-level file list or a pointer to the main language so the instructions can be tuned.
