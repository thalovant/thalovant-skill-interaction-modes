Last Edit: Claude Code (Claude Sonnet 5.5) - 2026-11-10 - Motive: Standard README (say it, install, settings, languages, develop).

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/thalovant/.github/main/profile/assets/thalovant-logo-dark.png">
    <img src="https://raw.githubusercontent.com/thalovant/.github/main/profile/assets/thalovant-logo-light.png" alt="Thalovant" width="240">
  </picture>
</p>

# Interaction Modes

[![Test](https://github.com/thalovant/thalovant-skill-interaction-modes/actions/workflows/test.yml/badge.svg)](https://github.com/thalovant/thalovant-skill-interaction-modes/actions/workflows/test.yml)

Switch your hub into party mode and back, per room or screen.

## Say it

- “Switch to party mode” → Party mode is on for this client.
- “Enable party mode” → Party mode is on for this client.
- “What mode are we in” → Party mode is on.
- “Which mode is active” → Tells you the mode, for example "Normal mode is on."
- French: “Passe en mode fête” → Le mode fête est activé.

Modes apply to the room or screen you are talking to, not the whole house.

## Install

Open the Thalovant marketplace on your hub and add **Interaction Modes**. Or install it yourself:

```sh
pip install thalovant-skill-interaction-modes
```

## Languages

65 languages and regional variants, including English, French, Spanish, German ([full list](thalovant_skill_interaction_modes/locale/supported.json)).

## Develop

```sh
pip install -e ".[test]"
python -m pytest test
```

Pull requests are tested on every change ([workflow](https://github.com/thalovant/thalovant-skill-interaction-modes/actions/workflows/test.yml)).

## Licence

Apache-2.0.
