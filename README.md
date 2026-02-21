# Evidence Factory (POC)

This repository is a proof-of-concept **evidence factory** for ML systems: it turns governance requirements into **machine-verifiable evidence** and enforces them with **policy-as-code** in CI.

**Design goal:** make governance constraints compile.

## Scope

- **Low-risk** POC scenario (advisory/drafting use, human review required).
- **Synthetic data only**.
- Model-in-the-box (the model is a build artifact produced by this repo).
- This is a **kernel**, not a platform: no dashboards, no bespoke infra.

This POC supports parts of AI Act–style obligations (traceability, documentation inputs, risk notes, oversight plan, etc.) by producing verifiable evidence artifacts. It does **not** by itself constitute full legal compliance.

## Repository layout

- `src/` — training + evaluation code
- `scripts/` — evidence assembly utilities
- `docs/` — **governance inputs** (bundled + hashed + gated)
- `policy/` — OPA/Rego policies executed by Conftest
- `.github/workflows/` — CI pipelines
- `evidence/` — generated artifacts (never hand-edited; usually gitignored)
- `build/` — generated model artifacts (usually gitignored)

## Governance inputs (`docs/`)

The `docs/` folder is reserved for governance inputs that are treated as **required evidence** and included in the evidence bundle. Filenames are treated as a stable API.

Expected files (minimum kernel):

- `docs/intended-purpose.md`
- `docs/human-oversight.md`
- `docs/data-governance.md`
- `docs/risk-notes.md`
- `docs/traceability.md`

For agent conventions and enforcement (e.g. not adding/renaming these without alignment), see **AGENTS.md** § Repo conventions.

## Architecture

### Two-layer model

**Governance kernel (definition)**

- Defines required evidence and invariants (via stable filenames + schemas + policy rules).
- Establishes what must exist for a build/release to be considered acceptable.
- (Optionally later) defines exception/waiver semantics.

**Evidence factory (enforcement)**

- Trains a small model.
- Runs evaluation.
- Generates supply-chain artifacts (SBOM, vulnerability scan).
- Assembles a deterministic evidence bundle with a hash manifest.
- Validates the bundle with policy-as-code.
- (On main) signs the bundle for tamper-evidence.

### Evidence bundle contract

Each CI run produces:

- `evidence/manifest.json` — list of included files with SHA256 hashes (the primary receipt)
- model artifacts + metadata (`model.joblib`, `train_meta.json`, etc.)
- `eval.json` — evaluation report tied to the model artifact
- governance docs copied from `docs/`
- CI-only artifacts:
  - `sbom.spdx.json`
  - `trivy.sarif`
- `evidence-pack.tgz` — portable bundle containing the above

The manifest is the main object validated by policy-as-code.

## Policy-as-code gates

Policies live in `policy/` and are executed by **Conftest** against `evidence/manifest.json`.

Gates are intentionally strict about:

- required evidence presence
- basic structural sanity (e.g., non-empty docs)
- CI-only requirements (SBOM and vuln scan outputs)

Policy failures must be **actionable** (e.g., “missing required file: docs/human-oversight.md”).

## CI workflow (high level)

On PR:

1. train + eval (small, deterministic)
2. generate SBOM
3. run vuln scan (Trivy; workflow fails on HIGH/CRITICAL — fix or ignore before merge)
4. assemble evidence bundle + manifest
5. run policy gates
6. upload evidence artifacts

On push to `main`:

- optionally sign the evidence bundle (keyless signing) and upload signature artifacts

CI is the source of truth.

## Engineering principles

This repo follows a reproducible / declarative / supply-chain–aware style:

- reproducible / hermetic behavior (pinned versions, explicit dependencies)
- immutable / append-only evidence (new evidence per meaningful change)
- content-addressed artifacts (hashes as identity)
- idempotent automation (safe to rerun)
- policy-as-code enforcement (OPA/Conftest)
- least privilege (minimize and scope credentials)
- fail fast / loud / actionable
- receipts before dashboards
- strict on evidence presence before strict thresholds (initially)

## Development workflow

This repo is environment-agnostic. One supported workflow is developing inside a sandbox VM with browser-only access.

Guidelines:

- run commands in the sandbox environment
- keep the workstation a thin client
- use minimal, repo-scoped GitHub credentials
- do not store tokens in tracked files

For how AI agents should work in this repo (branching, diffs, verification, change policy), see **AGENTS.md**.

## Anonymity and data handling

This repo must not contain sensitive data: synthetic data only; no secrets, internal URLs, PII, or internal docs. Full list and agent enforcement: **AGENTS.md** § Anonymity and data handling. If unsure, omit the material and leave a TODO.

## Local quickstart (example)

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
#   .venv\Scripts\activate
pip install -r requirements.txt

python src/train.py --out-dir build --seed 42
python src/eval.py --build-dir build --out build/eval.json
python scripts/make_evidence_pack.py --build-dir build --docs-dir docs --evidence-dir evidence --out-tgz evidence/evidence-pack.tgz
```

**Policy (local vs CI):** The full Conftest policy requires SBOM and Trivy outputs in the evidence dir. In CI they are produced before the evidence pack is assembled. For a quick local run you can omit them; the policy gate will fail until SBOM/Trivy are present (e.g. run the full pipeline in a VM or rely on CI as source of truth).

