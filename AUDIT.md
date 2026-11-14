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

## 2026-11-03: filelock split by Python version

- Finding: [GHSA-69hj-f68j-2879](https://github.com/tox-dev/filelock/security/advisories/GHSA-69hj-f68j-2879) (published after the 2026-10-25 review) affects every filelock release up to 4.2.0, so the `filelock==3.20.3` pin was no longer outside every advisory range. 4.2.1 is the first fixed release, and filelock 4.1.1+ requires Python 3.11. CodeRabbit raised this on #24.
- Second finding: the hub runtime installs skills with constraints that require `filelock>=4.2.1,<5`, so a wheel declaring `filelock==3.20.3` could not be installed on a hub (`uv pip install` reports no solution).
- Change: [requirements.txt](requirements.txt), and therefore the wheel metadata, now declares `filelock==3.20.3; python_version < "3.11"` and `filelock>=4.2.1,<5; python_version >= "3.11"`. The published combo-lock 0.3.1 requires `filelock~=3.0`, so installs on 3.11+ use the reviewed combo-lock build the hub runtime ships. uv picks it up from `[tool.uv] override-dependencies` in [pyproject.toml](pyproject.toml), which is pinned to a commit (uv does not check the `#sha256=` fragment on an override), and pip from [.github/ci/runtime-security-requirements.txt](.github/ci/runtime-security-requirements.txt), whose SHA-256 is checked, which [.github/scripts/check_installed.py](.github/scripts/check_installed.py) now passes.
- Tests: [test_dependency_security.py](test/test_dependency_security.py) checks both marker lines in the metadata and in requirements.txt, the installed filelock for the running interpreter, that both install routes name the same combo-lock archive and hash, and on 3.11+ that the installed combo-lock is the reviewed build.
- Residual risk (Python 3.10): no fixed filelock installs on 3.10. 3.20.3 remains the least-affected release there, with GHSA-69hj-f68j-2879 and the Windows-only GHSA-8mx5-7m5m-r77g. Hubs run Python 3.14, so the platform does not take this path.
- Residual risk (plain installs): a plain `pip install` from PyPI on 3.11+ without the reviewed combo-lock fails to resolve, rather than installing an affected filelock. This lasts until a published combo-lock accepts filelock 4.2.1+.
- Verification (local): Python 3.10 suite 366 passed, 1 skipped (filelock 3.20.3, published combo-lock); Python 3.14 suite 367 passed (filelock 4.2.7, combo-lock 0.3.1+thalovant.1). The installed-wheel check on 3.12 passed (360 passed). A hub-style install of the built wheel under `filelock>=4.2.1,<5` constraints succeeded, and the old metadata failed to resolve under the same constraints.

## 2026-11-03: filelock split follow-up

- Finding (independent review): uv does not verify the `#sha256=` fragment on a `[tool.uv] override-dependencies` URL, so the uv route was commit-pinned only, not hash-pinned as the comments said. pip and direct `-r` requirements do verify it, and so does the runtime image.
- Change: the uv installs in [test.yml](.github/workflows/test.yml) and [release.yml](.github/workflows/release.yml) now also pass `-r .github/ci/runtime-security-requirements.txt`, so CI and this repository's release install check the archive hash. The release step passes it only when the checked-out tag has the file, so tags made before the change can still be re-released. A deliberately wrong hash fails the install. The shared release workflow still relies on the commit-pinned override. The comment in [pyproject.toml](pyproject.toml) says so.
- Change: the 3.10 override is `combo-lock>=0.3,<0.4`, keeping the caps the published dependants put on it.
- Tests: [test_dependency_security.py](test/test_dependency_security.py) now compares the override list and the CI requirements file entry by entry: archive and hash, markers, the filelock range and the certifi floor. Altering the filelock marker, the certifi floor or the 3.10 override range each fails it.
- Verification (local): Python 3.10, 366 passed and 1 skipped (filelock 3.20.3, combo-lock 0.3.1); Python 3.14, 367 passed (filelock 4.2.7, combo-lock 0.3.1+thalovant.1), both installed with the CI command.

