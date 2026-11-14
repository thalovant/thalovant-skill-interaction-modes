# Quick facts

| Field | Value |
|---|---|
| Package | `thalovant-skill-interaction-modes` |
| Python | 3.10 or newer |
| SkillKit | 0.24.2 or newer |
| Entry point | `ovos.plugin.skill: thalovant-skill-interaction-modes.thalovant` |
| Skill class | `thalovant_skill_interaction_modes:InteractionModesSkill` |
| Languages | 65 packaged locales, plus compatible regional fallback |
| Default duration | 30 minutes |
| License | [Apache-2.0](LICENSE) |

See [releases](https://github.com/thalovant/thalovant-skill-interaction-modes/releases)
for versions and [the reference](REFERENCE.md) for settings and helper examples.

## Dependency constraint (2026-11-03)

- Current package: `thalovant-skill-interaction-modes` 0.1.11; no version bump or release.
- Runtime pin: `filelock==3.20.3; python_version < "3.11"` and `filelock>=4.2.1,<5; python_version >= "3.11"` in [requirements.txt](requirements.txt) and the install metadata produced by [setup.py](setup.py).
- Reviewed combo-lock build on 3.11+: `[tool.uv] override-dependencies` in [pyproject.toml](pyproject.toml) and [.github/ci/runtime-security-requirements.txt](.github/ci/runtime-security-requirements.txt).
- Entry point: `ovos.plugin.skill`, `thalovant-skill-interaction-modes.thalovant=thalovant_skill_interaction_modes:InteractionModesSkill`.
- Verification and advisory boundary: [AUDIT.md](AUDIT.md), [dependency tests](test/test_dependency_security.py).
