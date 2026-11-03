Last Edit: Claude Code - 2026-11-03 - Motive: Split the filelock requirement by Python version so 3.11+ installs only fixed releases and hub installs resolve.

# Suggestions

## 2026-09-30: keep repository metadata consistent

- Opportunity: a package declaration alone can leave the repository license undiscoverable.
- Proposal: include a root-license existence check in the packaging checks and compare it with declared terms when available.
- Estimated impact: low maintenance effort; prevents recurrence of the missing [LICENSE](LICENSE). Reference: [QUICK_FACTS.md](QUICK_FACTS.md).

## 2026-10-25: Keep the dependency decision current

- Problem: a future advisory or Python-support change can invalidate a currently reviewed pin.
- Proposal: recheck the published ranges before changing the split filelock requirement (3.20.3 on 3.10, `>=4.2.1,<5` on 3.11+), and drop the 3.10 line and the reviewed combo-lock override once a published combo-lock accepts filelock 4.2.1+. Then rerun [installed-metadata and lock behavior tests](test/test_dependency_security.py), sdist/wheel checks and normal CI.
- Estimated impact: a small recurring review; no runtime feature change or release is implied.
