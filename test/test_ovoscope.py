"""Real OVOS fallback routing, speech language and originating-session checks."""
from pathlib import Path

import pytest

ovoscope = pytest.importorskip("ovoscope")
from ovos_bus_client.message import Message
from ovos_bus_client.session import Session
from thalovant_skillkit.testing_ovos import capture_turn, managed_minicroft
import thalovant_skill_interaction_modes
from thalovant_skill_interaction_modes import InteractionModesSkill

SKILL_ID = "thalovant-skill-interaction-modes.thalovant"


class ScopeSkill(InteractionModesSkill):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("resources_dir", str(Path(thalovant_skill_interaction_modes.__file__).parent))
        super().__init__(*args, **kwargs)


@pytest.fixture
def minicroft():
    with managed_minicroft(
        [SKILL_ID], extra_skills={SKILL_ID: ScopeSkill},
        default_pipeline=ovoscope.FALLBACK_PIPELINE,
        lang="en-US", secondary_langs=["fr-FR"], max_wait=20,
    ) as croft:
        yield croft


@pytest.mark.parametrize("lang, utterance", [('en-US', 'enable party mode'), ('fr-FR', 'active le mode fête')])
def test_native_fallback_preserves_speaker_and_language(minicroft, lang, utterance):
    session = Session(f"scope-{lang}")
    session.lang = lang
    session.pipeline = ovoscope.FALLBACK_PIPELINE
    source = Message(
        "recognizer_loop:utterance", {"utterances": [utterance], "lang": lang},
        {"session": session.serialize(), "source": "household-test", "destination": "skills"},
    )
    turn = capture_turn(minicroft, source, timeout=10)
    assert turn.spoken and all(turn.spoken)
    matches = turn.of_type("ovos.intent.matched")
    assert any(message.data.get("skill_id") == SKILL_ID for message in matches)
    speech = turn.of_type("ovos.utterance.speak") or turn.of_type("speak")
    assert all(message.data["lang"] == lang for message in speech)
    assert all(message.context["session"]["session_id"] == session.session_id for message in speech)
