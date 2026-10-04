"""Real OVOS fallback routing, speech language and originating-session checks."""
import json
from pathlib import Path

import pytest

ovoscope = pytest.importorskip("ovoscope")
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from thalovant_skillkit.testing_ovos import capture_turn, managed_minicroft
import thalovant_skill_interaction_modes
from thalovant_skill_interaction_modes import (
    InteractionModesSkill, LOCALE_DIR, RESOURCES, get_interaction_mode, reset_interaction_modes,
)

SKILL_ID = "thalovant-skill-interaction-modes.thalovant"


class ScopeSkill(InteractionModesSkill):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("resources_dir", str(Path(thalovant_skill_interaction_modes.__file__).parent))
        super().__init__(*args, **kwargs)


@pytest.fixture(scope="module")
def minicroft():
    with managed_minicroft(
        [SKILL_ID], extra_skills={SKILL_ID: ScopeSkill},
        default_pipeline=ovoscope.FALLBACK_PIPELINE,
        lang="en-US", secondary_langs=["fr-FR"], max_wait=20,
    ) as croft:
        yield croft


@pytest.mark.parametrize("lang", json.loads((LOCALE_DIR / "supported.json").read_text())["locales"]
                         + ["en-IE", "it-CH", "ar-EG", "zh-Hant-HK"])
def test_native_fallback_preserves_speaker_and_language(minicroft, lang):
    reset_interaction_modes()
    session = Session(f"scope-{lang}")
    session.lang = lang
    session.pipeline = ovoscope.FALLBACK_PIPELINE
    for intent, dialog, expected in (
        ("party.mode.enable", "party.mode.enabled", "party"),
        ("interaction.mode.status", "party.mode.status", "party"),
        ("party.mode.disable", "party.mode.disabled", None),
    ):
        utterance = RESOURCES.lines(lang, "", intent + ".intent", fallback=False)[0]
        source = Message(
            "recognizer_loop:utterance", {"utterances": [utterance], "lang": lang},
            {"session": session.serialize(), "source": "household-test", "destination": "skills"},
        )
        turn = capture_turn(minicroft, source, timeout=10)
        assert turn.spoken and all(turn.spoken)
        assert all(text in RESOURCES.dialog_lines(dialog, lang) for text in turn.spoken)
        matches = turn.of_type("ovos.intent.matched")
        assert any(message.data.get("skill_id") == SKILL_ID for message in matches)
        speech = turn.of_type("ovos.utterance.speak") or turn.of_type("speak")
        assert all(message.data["lang"] == lang for message in speech)
        assert all(message.context["session"]["session_id"] == session.session_id for message in speech)
        assert get_interaction_mode(source) == expected
