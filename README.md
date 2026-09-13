# Interaction Modes

Temporary session modes for Thalovant hubs.

This skill lets a client say things like "turn on party mode" or "back to normal" without changing hub configuration, OVOS core, or HiveMind core. The active mode is stored in process memory and scoped to the current HiveMind `site_id`, so one client can be in party mode while another client connected to the same hub remains normal.

## Design

- State is in memory and expires automatically.
- The scope key comes from `message.context["session"]["site_id"]`.
- Participating Thalovant skills opt in by importing the helper functions from this package.
- Runtime restarts clear modes by design.
- API and public web previews should pass mode explicitly instead of relying on hidden sticky state.

## Helper API

```python
from thalovant_skill_interaction_modes import get_interaction_mode, is_interaction_mode

if is_interaction_mode(message, "party"):
    ...
```

Available helpers:

- `set_interaction_mode(message, mode, ttl_seconds=1800)`
- `get_interaction_mode(message)`
- `clear_interaction_mode(message)`
- `is_interaction_mode(message, mode)`

## Languages

Every locale listed in
`thalovant_skill_interaction_modes/locale/supported.json` is packaged with a
complete intent, vocabulary, dialog, and metadata contract.

## Session and reliability behavior

- Mode state uses SkillKit's synchronized `SessionStateStore`, capped at 1,024 scopes. A new scope evicts the oldest written scope when capacity is reached.
- The default expiry is 30 minutes; the `mode_ttl_seconds` setting changes it. Expiry uses monotonic time, so wall-clock changes cannot prolong a mode. Reading a mode does not refresh its expiry.
- The scope is the session's site ID, then session ID, then a client/site/source identity from the message context. Requests without a usable identity cannot enable a mode.
- State is shared by this package's helper API and skill within one Python process. Separate runtime processes have separate mode state; restarting clears it.

## Verification and contributing

Use Python 3.10 or newer and install the test extra so the OVOScope tests run:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --pre -e ".[test]" build
python -m pytest -q
python -m build
thalovant-skillkit check-artifacts . --wheel dist/*.whl --sdist dist/*.tar.gz
```

CI runs the complete test suite on Python 3.10, 3.12 and 3.14. Tests isolate
OVOS configuration and settings from the developer's real assistant. Native
OVOScope tests check the actual fallback pipeline and speech/session metadata;
unit tests cover the skill's deterministic behavior and failure cases.

The package includes resources for the 46 locales declared in
`thalovant_skill_interaction_modes/locale/supported.json`. Resource and packaging checks verify the
files that ship; native OVOS scenarios currently cover English and French.
Native-speaker review and testing with the intended listeners are still needed
to judge natural phrasing, pronunciation and understanding in every locale.
