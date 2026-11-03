Last Edit: Claude Code - 2026-11-03 - Motive: Split the filelock requirement by Python version so 3.11+ installs only fixed releases and hub installs resolve.

# Common questions

## Will this play music or change every speaker?

No. Party mode lets participating skills make their replies more playful.
It applies to the speaker that asked. Other speakers keep their own modes.

## How do I stop it?

Say “Back to normal”. It also expires after 30 minutes by default, or when the
assistant restarts. [Change the duration](REFERENCE.md#try-it) if needed.

## Which languages work?

The skill includes [65 language and regional resource sets](thalovant_skill_interaction_modes/locale/supported.json).
SkillKit also handles compatible regional variants. Recognition and voice
availability depend on your speech providers.

## Who made it?

[Thalovant contributors](README.md#credits), using OpenVoiceOS and SkillKit.
The skill is Python software, licensed under [Apache-2.0](LICENSE).

## Why is filelock pinned differently on Python 3.10?

filelock up to 4.2.0 is inside published advisory ranges, and 4.2.1, the first fixed release, needs Python 3.11. So the skill requires `filelock>=4.2.1,<5` on 3.11+ and keeps 3.20.3, the least-affected release, on 3.10. The published combo-lock caps filelock below 4, so installs on 3.11+ use the reviewed combo-lock build the hub runtime ships: uv gets it from `[tool.uv]` in [pyproject.toml](pyproject.toml), and pip from [.github/ci/runtime-security-requirements.txt](.github/ci/runtime-security-requirements.txt). A plain PyPI install on 3.11+ without it fails to resolve. See [AUDIT.md](AUDIT.md) and [the regression tests](test/test_dependency_security.py).
