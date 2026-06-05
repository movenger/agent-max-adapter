# Agent Instructions

## Scope
- Repo purpose: production-grade integration between MAX Bot API and Hermes Agent.
- Keep docs and specs in `docs/`; do not add product code until spec/contracts are written.

## Commands
- Create venv: `python -m venv .venv`
- Activate: `source .venv/bin/activate`
- List files: `find . -maxdepth 3 -type f | sort`

## File Ownership
- `docs/design/**`: UI/design specs only
- `docs/api/**`: external/internal API contracts
- `docs/specs/**`: architecture/specification docs
- `docs/research/**`: source notes, doc extracts, comparisons

## Conventions
- Prefer Markdown docs with explicit source links and dated notes.
- Record uncertain vendor facts as assumptions/open questions, not decisions.
- Do not commit secrets, tokens, or copied proprietary docs.
