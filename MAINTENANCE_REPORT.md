# Maintenance report

## 2026-09-30: license and language metadata

Added a root Apache-2.0 license, documented GitHub's detected languages (Python), and updated repository reference, audit, and navigation files. License basis: Existing [setup.py](setup.py) declaration.

Verification: `python -m pytest test -q --maxfail=1 --disable-warnings` — ModuleNotFoundError: No module named 'thalovant_skillkit'; collection blocked in the local environment.

### Transparency Report

- AI Model: GPT-6 (Codex).
- Actions Taken: inspected GitHub metadata, package declarations, source symbols and tests; added license text and documentation; checked the final diff.
- Oversight: the user requested the update and explicitly selected proprietary terms for repositories with no existing declaration. The assistant performed automated validation; no human line-by-line review is claimed.

Metadata validation: 116 checks passed across the 29 repositories (canonical license text, new documentation links and headers, source citations, and metadata-only change scope).

## 2026-10-25: Filelock compatibility pin

Pinned the actual package dependency and requirements install route to `filelock==3.20.3`; added three focused regression tests and updated maintenance navigation. No skill runtime behavior, permissions, catalog, package version or release workflow was changed.

Local Python 3.12.12 verification: tests: 365 passed in 6.77s. All three [dependency tests](test/test_dependency_security.py) pass. The sdist-to-wheel build and `thalovant-skillkit check-artifacts` pass; wheel `Requires-Dist` contains exactly `filelock==3.20.3`. The combined isolated skill environment passes `uv pip check`. Hosted CI remains a merge gate; other interpreter versions were not rerun locally.

### Transparency Report

Codex (exact runtime model identifier unavailable) inspected the install paths and primary advisories, added the pin/tests and ran local checks. The user authorized dependency remediation. Human review and hosted checks precede any merge; no skill release or deployment was performed.

## 2026-11-03: filelock split by Python version

Replaced the single `filelock==3.20.3` requirement with two lines split by marker: 3.20.3 on Python 3.10 and `>=4.2.1,<5` on 3.11+. Added the reviewed combo-lock build to both install routes: `[tool.uv] override-dependencies` in [pyproject.toml](pyproject.toml), and [.github/ci/runtime-security-requirements.txt](.github/ci/runtime-security-requirements.txt) for the pip install in [.github/scripts/check_installed.py](.github/scripts/check_installed.py). Rewrote [test_dependency_security.py](test/test_dependency_security.py) to guard the split. Reason and residual risk: [AUDIT.md](AUDIT.md). Skill behavior, version, catalog and release workflow are unchanged.

Verification (local): Python 3.10 suite 366 passed, 1 skipped; Python 3.14 suite 367 passed; installed-wheel check on 3.12 passed; a hub-style install of the wheel under the runtime's filelock constraint succeeded.

### Transparency Report

- AI Model: Claude Opus 5.5 (Claude Code).
- Actions Taken: checked the advisory ranges and filelock's Python support, reproduced the hub-install conflict, changed the requirement, the uv configuration, the CI requirements file and the installed-wheel script, rewrote the dependency guard tests, ran the suites on 3.10, 3.12 and 3.14, and updated the docs.
- Oversight: the change is reviewed through a pull request with hosted CI. No release, catalog change or deployment is part of it.

## 2026-11-03: filelock split follow-up

Added `-r .github/ci/runtime-security-requirements.txt` to the uv installs in the test and release workflows, so they check the combo-lock archive hash, which uv does not check on an override. The release step adds it only when the checked-out tag has the file, so older tags stay re-releasable. Corrected the [pyproject.toml](pyproject.toml) comment and [AUDIT.md](AUDIT.md) to match, capped the 3.10 override at `combo-lock>=0.3,<0.4`, and made the dependency guard tests compare the override list and the CI requirements file entry by entry. The new assertions were mutation-checked. Verification: Python 3.10 366 passed, 1 skipped; Python 3.14 367 passed.

### Transparency Report

- AI Model: Claude Opus 5.5 (Claude Code); the findings came from an independent Claude review agent.
- Actions Taken: verified that uv ignores the fragment on overrides and checks it on `-r` requirements, changed two workflow install lines, the override range and the guard test, ran the suites on 3.10 and 3.14, and updated the docs.
- Oversight: pull request with hosted CI; no release or deployment.

## 2026-11-10: 0.1.12, speech pacing and markup

- `SPEECH_STYLE` (skillkit 0.34) is declared, so a reply a translator writes as two sentences, or with a colon or a dash, is paced from its own words. Every reply the skill ships today is one short sentence, so nothing sounds different yet. The import is guarded: a hub keeps the skillkit it loaded until its runtime restarts, and on a kit older than 0.34 the skill loads and speaks plainly. The kit floor is unchanged.

Verification: full suite on skillkit 0.35.0: 370 passed; on skillkit 0.29.2: 368 passed, 2 skipped.

### Transparency Report

- AI Model: Claude Sonnet 5.5 (Claude Code).
- Actions Taken: declared the skill's `SPEECH_STYLE` behind a guarded import, adapted the reply code and tests, and ran the suite on the current skillkit and on skillkit 0.29.2.
- Oversight: automated test runs and CI; the maintainer reviews the pull request before release.
