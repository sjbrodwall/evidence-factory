# Evidence Factory: make governance compile.

This repository is a proof-of-concept evidence factory for ML systems: it turns governance requirements into cryptographically verifiable evidence and enforces them with policy-as-code in CI. If the governance requirements aren't met, the build fails. Retroactive falsification is detectable.  

**The evidence produced by this PoC does *not* by itself constitute full legal compliance.**

Verification layers:
1. **Existence:** the documentation files specified in evidence.rego exist and aren't empty. ✓ 
2. **Structure:** the documentation files include the structure for the information required by the AI Act.
3. **Coherence:** the information in the documentation is internally consistent and semantically valid.
4. **Grounded validity:** the documentation's claims about the system are true as the system and the world around it change.    

Currently the system is working at **layer 1** (verification of the existence of the specified files). Layer 2 is next on the docket; 3 and 4 are open research questions. 

## Table of contents

- [Scope](#scope)
- [Repository layout](#repository-layout)
- [Governance inputs (`governance/`)](#governance-inputs-governance)
- [Architecture](#architecture)
- [Policy-as-code gates](#policy-as-code-gates)
- [CI workflow (high level)](#ci-workflow-high-level)
- [Engineering principles](#engineering-principles)
- [Development workflow](#development-workflow)
- [Testing strategy](#testing-strategy)
- [Anonymity and data handling](#anonymity-and-data-handling)
- [Local quickstart (example)](#local-quickstart-example)

## Scope

This PoC uses a low-risk, decision-support scenario with synthetic data. The ML aspects are deliberately minimal; the governance architecture is the primary exhibit.  The model is a build artifact produced by the repo itself.  There are no dashboards or bespoke infra--this is a kernel, not a platform.  

## Repository layout

- `src/` — training + evaluation code
- `scripts/` — evidence assembly utilities
- `governance/` — **governance inputs** (JSON; bundled + hashed + gated)
- `policy/` — OPA/Rego policies executed by Conftest
- `.github/workflows/` — CI pipelines
- `tests/` — Python tests (pytest) for evidence assembly
- `evidence/` — generated artifacts (never hand-edited; gitignored)
- `build/` — generated model artifacts (gitignored)

## Governance inputs (`governance/`)

The `governance/` folder holds (barely) structured JSON governance inputs that are treated as **required evidence** and included in the evidence bundle. Filenames are treated as a stable API. Each file has `schema_version`, `title`, and `body`.

Expected files (minimum kernel):

- `governance/intended-purpose.json`
- `governance/human-oversight.json`
- `governance/data-governance.json`
- `governance/risk-notes.json`
- `governance/traceability.json`

For agent conventions and enforcement (e.g. not adding/renaming these without alignment), see AGENTS.md § Repo conventions.

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

- `evidence/manifest.json` — list of included files with SHA256 hashes (the primary receipt); in CI also includes `git_sha` and `ci_run_url` for auditability
- model artifacts + metadata (`model.joblib`, `train_meta.json`, etc.)
- `eval.json` — evaluation report tied to the model artifact
- governance JSON files copied from `governance/`
- CI-only artifacts:
  - `sbom.spdx.json`
  - `trivy.sarif`
- `evidence-pack.tgz` — portable bundle containing the above

The manifest is the main object validated by policy-as-code.

## Policy-as-code gates

Policies live in `policy/` and are executed by **Conftest** against `evidence/manifest.json`.

Gates are intentionally strict about:

- required evidence presence
- basic structural sanity (e.g., non-empty governance files)
- CI-only requirements (SBOM and vuln scan outputs)

Policy failures must be *actionable* (e.g., “missing required file: governance/human-oversight.json”).

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
- test the guarantee, not the structure
- strict on evidence presence before strict thresholds (initially)

## Development workflow

This repo is environment-agnostic. One supported workflow is developing inside a sandbox VM with browser-only access.

Guidelines:

- run commands in the sandbox environment
- keep the workstation a thin client
- use minimal, repo-scoped GitHub credentials
- do not store tokens in tracked files

For how AI agents should work in this repo (branching, diffs, verification, change policy), see AGENTS.md.

## Testing strategy

Tests are prioritized where the value proposition lives: evidence assembly and policy-as-code.

- **Evidence pack** — Tests for `scripts/make_evidence_pack.py` (and equivalent logic) should assert that the manifest covers exactly the expected files (required governance files, model artifacts, eval report, and when present SBOM/Trivy). That protects the evidence-assembly contract.
- **Policy** — Rego/Conftest tests for `policy/evidence.rego` ensure gates are not silently broken by refactors; policy is the main enforcement surface.

The ML code in `src/` (train + eval) is a minimal placeholder so the pipeline has model artifacts to bundle. Tests for train determinism or eval report schema are optional contract tests for that placeholder behavior; they are not the primary testing focus.

**Run tests locally:** `pip install -r requirements-dev.txt` then `python -m pytest tests/ -v`. Policy unit tests: `conftest verify --policy policy` (requires [Conftest](https://www.conftest.dev/)).

## Anonymity and data handling

This repo must not contain sensitive data: synthetic data only; no secrets, internal URLs, PII, or internal docs. Full list and agent enforcement: AGENTS.md § Anonymity and data handling. If unsure, omit the material and leave a TODO.

## Local quickstart (example)

Use Python 3.13 (CI and pinned deps use 3.13; see `.python-version`).

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
#   .venv\Scripts\activate
pip install -r requirements.txt

python src/train.py --out-dir build --seed 42
python src/eval.py --build-dir build --out build/eval.json
python scripts/make_evidence_pack.py --build-dir build --evidence-dir evidence --out-tgz evidence/evidence-pack.tgz
```

**Policy (local vs CI):** The full Conftest policy requires SBOM and Trivy outputs in the evidence dir. In CI they are produced before the evidence pack is assembled. For a quick local run you can omit them; the policy gate will fail until SBOM/Trivy are present (e.g. run the full pipeline in a VM or rely on CI as source of truth).

