# Interaction Modes

Give one speaker a temporary party mode. Participating skills can change their
replies while it is active; this skill itself does not start music or change volume.

## Try it

Say “Turn on party mode”, then “What mode are we in?” The skill confirms party
mode. Say “Back to normal” to end it. Another speaker keeps its own mode.

The `mode_ttl_seconds` skill setting controls the duration. The default is 1,800
seconds (30 minutes). Asking for the current mode does not extend that time.
Restarting the assistant clears modes.

## Use the mode in another skill

Use the same message that your SkillKit handler received:

```python
from thalovant_skill_interaction_modes import is_interaction_mode

# Inside your skill's handler:
if is_interaction_mode(message, "party"):
    self.speak_to(message, self.dialog("playful.answer", self.lang_of(message)))
else:
    self.speak_to(message, self.dialog("normal.answer", self.lang_of(message)))
```

Add those two dialog files to your skill's languages. The helper only reads the
mode; it does not extend its lifetime. Both skills must run in the same Python
process to share state.

The package also provides:

- `set_interaction_mode(message, "party", ttl_seconds=1800)` — returns whether it could set the mode.
- `get_interaction_mode(message)` — returns `"party"` or `None`.
- `clear_interaction_mode(message, mode=None)` — returns whether it removed a mode.
- `is_interaction_mode(message, "party")` — checks without changing anything.

State uses SkillKit's synchronized `SessionStateStore`, capped at 1,024 scopes.
The oldest written scope is evicted at capacity. Expiry follows elapsed time,
so clock corrections do not prolong a mode. Identity comes from the session's
site ID, then session ID, then a client/site/source identity in the message
context. Missing identities and framework placeholders cannot enable a mode.

`preview_reply(utterance, lang, context)` returns text without speaking or changing
state. Pass `commit=True` explicitly to apply a mode change. `preview_mode(context)`
reads the current mode.

## Languages

All 65 locales in [supported.json](thalovant_skill_interaction_modes/locale/supported.json)
ship complete command, reply, and metadata resources. SkillKit resolves additional
compatible regional variants; English is the default for unsupported languages.
A known English command also works on a non-English speaker and receives an
English reply. Other commands receive a reply in the requesting locale.

Mode changes require a complete command, so “party mode is a song title” cannot
switch modes. Status questions can include trailing context, such as
“What mode are we in Montreal?”

Shared regional wording comes from [regional.json](thalovant_skill_interaction_modes/locale/regional.json).
Edit the source locale or a regional override, then regenerate and check:

```bash
thalovant-skillkit locales --write
thalovant-skillkit check --no-fleet
```

Traditional and Simplified Chinese resources use written Mandarin. Resource
coverage and automated tests do not certify native-speaker fluency. Recognition
and pronunciation depend on your speech providers.

## Develop and verify

Use Python 3.10 or newer and SkillKit 0.24.2 or newer:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --pre -e ".[test]" build
python -m pytest -q
python -m build
thalovant-skillkit check-artifacts . --wheel dist/*.whl --sdist dist/*.tar.gz
```

Tests isolate assistant settings from your own configuration. Every packaged
command is checked for the correct action. OVOScope runs enable, status, and
disable turns for every declared locale, checking the reply text, language,
originating session, and stored mode. Additional tests cover room isolation,
expiry, read-only previews, malformed settings, and unrelated requests.
