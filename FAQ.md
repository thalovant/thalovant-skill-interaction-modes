Last Edit: Codex (exact runtime model identifier unavailable) - 2026-10-25 - Motive: Record the scoped filelock compatibility pin and verification.

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

## Why is filelock pinned to 3.20.3?

The pin keeps the skill's Python 3.10-compatible dependency route outside the eight reviewed advisory ranges without adding a newer-runtime-only dependency. Both requirements installs and built wheel metadata enforce it. It must be reassessed when advisories or runtime support change; it is not a permanent security guarantee. See [AUDIT.md](AUDIT.md) and `test_installed_metadata_pins_reviewed_filelock` in [the regression tests](test/test_dependency_security.py).
