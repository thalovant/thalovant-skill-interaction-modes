from ovos_bus_client.message import Message

from thalovant_skill_interaction_modes import (
    FALLBACK_PRIORITY,
    InteractionModesSkill,
    clear_interaction_mode,
    get_interaction_mode,
    is_interaction_mode,
    reset_interaction_modes,
    set_interaction_mode,
)


def setup_function():
    reset_interaction_modes()


def message(site_id: str = "kitchen"):
    return Message(
        "test",
        {},
        {"session": {"site_id": site_id, "session_id": f"{site_id}-session"}},
    )


def utterance_message(utterance: str, site_id: str = "kitchen", lang: str = "en-US"):
    return Message(
        "recognizer_loop:utterance",
        {"utterance": utterance, "utterances": [utterance], "lang": lang},
        {"lang": lang, "session": {"site_id": site_id, "session_id": f"{site_id}-session"}},
    )


def test_mode_is_scoped_per_site_id():
    kitchen = message("kitchen")
    office = message("office")

    assert set_interaction_mode(kitchen, "party")
    assert get_interaction_mode(kitchen) == "party"
    assert is_interaction_mode(kitchen, "party")
    assert get_interaction_mode(office) is None

    assert clear_interaction_mode(kitchen, "party")
    assert get_interaction_mode(kitchen) is None


def test_mode_expires(monkeypatch):
    now = 1000.0
    monkeypatch.setattr("thalovant_skill_interaction_modes.time.time", lambda: now)
    client = message("short")

    assert set_interaction_mode(client, "party", ttl_seconds=1)
    assert get_interaction_mode(client) == "party"

    now = 1002.0
    assert get_interaction_mode(client) is None


class HarnessSkill(InteractionModesSkill):
    def __del__(self):
        pass

    @property
    def lang(self):
        return "en-US"

    @property
    def settings(self):
        return {"mode_ttl_seconds": 60}


def test_skill_handlers_speak_localized_status(monkeypatch):
    spoken = []
    skill = HarnessSkill.__new__(HarnessSkill)
    skill.speak = spoken.append

    skill.handle_party_mode_enable(message("living-room"))
    assert get_interaction_mode(message("living-room")) == "party"
    assert "Party mode" in spoken[-1]

    skill.handle_interaction_mode_status(message("living-room"))
    assert "Party mode" in spoken[-1]

    skill.handle_party_mode_disable(message("living-room"))
    assert get_interaction_mode(message("living-room")) is None
    assert spoken[-1]


def test_preview_reply_can_mutate_and_read_mode():
    skill = HarnessSkill.__new__(HarnessSkill)
    context = {"session": {"site_id": "living-room", "session_id": "preview-request"}}

    assert "Party mode" in skill.preview_reply(
        "Switch to party mode.",
        "en-US",
        context,
        commit=True,
    )
    assert get_interaction_mode(message("living-room")) == "party"
    assert "Party mode" in skill.preview_reply(
        "What interaction mode is on?",
        "en-US",
        context,
    )
    assert "Party mode" in skill.preview_reply(
        "What mode am I in?",
        "en-US",
        context,
    )
    assert skill.preview_reply("Switch to work mode.", "en-US", context, commit=True)
    assert get_interaction_mode(message("living-room")) is None
    assert skill.preview_reply("Switch to work mode.", "en-US", context, commit=True) in {
        "Normal mode is on.",
        "This client is in normal mode.",
    }


def test_switch_mode_synonyms_are_classified():
    skill = HarnessSkill.__new__(HarnessSkill)

    assert skill.can_answer(utterance_message("switch to party mode", "living-room", "en-US"))
    assert skill.can_answer(utterance_message("switch to work mode", "living-room", "en-US"))
    assert skill.can_answer(utterance_message("passe en mode fete", "living-room", "fr-FR"))
    assert skill.can_answer(utterance_message("passe en mode travail", "living-room", "fr-FR"))


def test_preview_reply_without_commit_does_not_mutate_mode():
    skill = HarnessSkill.__new__(HarnessSkill)
    context = {"session": {"site_id": "living-room", "session_id": "preview-request"}}

    assert skill.preview_reply("Enable party mode.", "en-US", context, commit=False)
    assert get_interaction_mode(message("living-room")) is None


def test_status_fallback_claims_trailing_context_and_french_status():
    spoken = []
    skill = HarnessSkill.__new__(HarnessSkill)
    skill.speak = spoken.append

    english = utterance_message("what mode are we in Montreal", "living-room", "en-US")
    assert skill.can_answer(english)
    assert skill._fallback_answer(english) is True
    assert spoken[-1] in {"Normal mode is on.", "This client is in normal mode."}

    spoken.clear()
    singular_english = utterance_message("what mode am I in", "living-room", "en-US")
    assert skill.can_answer(singular_english)
    assert skill._fallback_answer(singular_english) is True
    assert spoken[-1] in {"Normal mode is on.", "This client is in normal mode."}

    spoken.clear()
    natural_english = utterance_message("what interaction mode is on", "living-room", "en-US")
    assert skill.can_answer(natural_english)
    assert skill._fallback_answer(natural_english) is True
    assert spoken[-1] in {"Normal mode is on.", "This client is in normal mode."}

    french = utterance_message("quel mode est actif", "living-room", "fr-FR")
    assert skill.can_answer(french)
    assert skill._fallback_answer(french) is True
    assert spoken[-1] in {"Le mode normal est actif.", "Ce client est en mode normal."}

    spoken.clear()
    natural_french = utterance_message("dans quel mode suis je", "living-room", "fr-FR")
    assert skill.can_answer(natural_french)
    assert skill._fallback_answer(natural_french) is True
    assert spoken[-1] in {"Le mode normal est actif.", "Ce client est en mode normal."}

    spoken.clear()
    live_shape = Message(
        "ovos.skills.fallback.thalovant-skill-interaction-modes.thalovant.request",
        {"utterance": "quel mode est actif", "lang": "en-US"},
        {"session": {"site_id": "living-room", "session_id": "living-room-session"}},
    )
    assert skill.can_answer(live_shape)
    assert skill._fallback_answer(live_shape) is True
    assert spoken[-1] in {"Le mode normal est actif.", "Ce client est en mode normal."}


def test_fallback_priority_runs_in_low_pipeline():
    assert FALLBACK_PRIORITY > 90
