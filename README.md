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

- `en-US`
- `fr-FR`
