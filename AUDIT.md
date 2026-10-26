Last Edit: Codex (exact runtime model identifier unavailable) - 2026-10-25 - Motive: Record the scoped filelock compatibility pin and verification.

# Audit

## 2026-09-30: license and language metadata

- Fixed: missing root license text. Added [Apache-2.0](LICENSE), based on Existing [setup.py](setup.py) declaration.
- Manual review: GitHub already reports Python; no language override is necessary. Source evidence: [`InteractionModesSkill`](thalovant_skill_interaction_modes/__init__.py#L132), [`InteractionModesSkill.mode_ttl_seconds`](thalovant_skill_interaction_modes/__init__.py#L141).
- Baseline verification: `python -m pytest test -q --maxfail=1 --disable-warnings` — ModuleNotFoundError: No module named 'thalovant_skillkit'; collection blocked in the local environment.
- Test evidence: [test/test_contract.py](test/test_contract.py). Runtime code and test files are unchanged by this metadata update.

Metadata validation: 116 checks passed across the 29 repositories (canonical license text, new documentation links and headers, source citations, and metadata-only change scope).

## 2026-10-25: Filelock dependency boundary

[requirements.txt](requirements.txt) and [setup.py](setup.py) now constrain real installs, not scanner input. [test_dependency_security.py](test/test_dependency_security.py) checks installed metadata, requirements agreement and actual `FileLock.acquire` exclusion/reuse.

The reviewed exact pin is outside all eight published affected ranges checked on 2026-10-25. It includes the earlier fixes and avoids the features introduced by later affected releases:

- Earlier fixes: [GHSA-w853-jp5j-5j7f](https://github.com/tox-dev/filelock/security/advisories/GHSA-w853-jp5j-5j7f), [GHSA-qmgc-5h2g-mvrw](https://github.com/tox-dev/filelock/security/advisories/GHSA-qmgc-5h2g-mvrw).
- Affected from 3.20.4 through 4.2.0: [GHSA-v4x8-3wr5-3wq8](https://github.com/tox-dev/filelock/security/advisories/GHSA-v4x8-3wr5-3wq8), [GHSA-9vhv-jxww-xfm5](https://github.com/tox-dev/filelock/security/advisories/GHSA-9vhv-jxww-xfm5).
- Affected from 3.22.0 through 4.2.0: [GHSA-567q-5qvw-pf92](https://github.com/tox-dev/filelock/security/advisories/GHSA-567q-5qvw-pf92).
- Affected from 4.1.0 through 4.2.0: [GHSA-jqc4-5cvw-7w85](https://github.com/tox-dev/filelock/security/advisories/GHSA-jqc4-5cvw-7w85), [GHSA-2g95-wg33-c5x2](https://github.com/tox-dev/filelock/security/advisories/GHSA-2g95-wg33-c5x2), [GHSA-crv4-6mhj-j5jh](https://github.com/tox-dev/filelock/security/advisories/GHSA-crv4-6mhj-j5jh).

This is a dependency selection, not a scanner waiver or proof against future advisories. No security check is suppressed.

Local Python 3.12.12 verification: tests: 365 passed in 6.77s. All three [dependency tests](test/test_dependency_security.py) pass. The sdist-to-wheel build and `thalovant-skillkit check-artifacts` pass; wheel `Requires-Dist` contains exactly `filelock==3.20.3`. The combined isolated skill environment passes `uv pip check`. Hosted CI remains a merge gate; other interpreter versions were not rerun locally.
