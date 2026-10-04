"""Exercise each shipped command, its language, and its isolated state."""
import json

import pytest
from ovos_bus_client.message import Message

from thalovant_skill_interaction_modes import (
    LOCALE_DIR, RESOURCES, _classify_utterance_match, get_interaction_mode,
    reset_interaction_modes,
)
from test_interaction_modes import HarnessSkill, utterance_message

LOCALES = json.loads((LOCALE_DIR / "supported.json").read_text())["locales"]
INTENTS = {
    "enable": "party.mode.enable.intent",
    "disable": "party.mode.disable.intent",
    "status": "interaction.mode.status.intent",
}


@pytest.fixture(autouse=True)
def clean_modes():
    reset_interaction_modes()
    yield
    reset_interaction_modes()


@pytest.mark.parametrize("lang", LOCALES)
@pytest.mark.parametrize("action,filename", INTENTS.items())
def test_every_published_phrase_matches_its_action(lang, action, filename):
    for phrase in RESOURCES.lines(lang, "", filename, fallback=False):
        assert _classify_utterance_match(phrase, lang) == (action, lang), phrase


@pytest.mark.parametrize("lang", LOCALES)
def test_localized_round_trip_and_room_isolation(lang):
    skill = HarnessSkill.__new__(HarnessSkill)
    spoken = []
    skill.speak_to = lambda source, text, **kw: spoken.append((source, text, kw["lang"]))
    other_room = utterance_message("", "other-room", lang)
    for action, dialog, expected in (
        ("enable", "party.mode.enabled", "party"),
        ("status", "party.mode.status", "party"),
        ("disable", "party.mode.disabled", None),
        ("status", "interaction.mode.normal", None),
    ):
        phrase = RESOURCES.lines(lang, "", INTENTS[action], fallback=False)[0]
        source = utterance_message(phrase, "this-room", lang)
        assert skill.handle_fallback(source)
        assert spoken[-1][0] is source
        assert spoken[-1][1] in RESOURCES.dialog_lines(dialog, lang)
        assert spoken[-1][2] == lang
        assert get_interaction_mode(source) == expected
        assert get_interaction_mode(other_room) is None


@pytest.mark.parametrize("phrase", [
    "turn on party mode in a story", "party mode is a terrible idea",
    "disable party mode is what she said", "normal mode is a song title",
])
def test_unrelated_suffix_cannot_change_a_mode(phrase):
    skill = HarnessSkill.__new__(HarnessSkill)
    assert not skill.handle_fallback(utterance_message(phrase))


def test_english_on_french_speaker_reports_the_matched_language():
    assert _classify_utterance_match("enable party mode", "fr-CA") == ("enable", "en-US")


@pytest.mark.parametrize("lang,expected", [("en-IE", "en"), ("it-CH", "it"),
                                         ("ar-EG", "ar"), ("zh-Hant-HK", "zh")])
def test_additional_regions_use_compatible_resources(lang, expected):
    resolved = RESOURCES.lang(lang)
    assert resolved.split("-")[0] == expected
    phrase = RESOURCES.lines(resolved, "", INTENTS["enable"])[0]
    assert _classify_utterance_match(phrase, lang) == ("enable", lang)


@pytest.mark.parametrize("context", [
    {}, {"session": {"session_id": "default"}},
    {"session": {"session_id": "unknown"}},
    {"session": {"site_id": "unknown", "session_id": "default"}, "source": "skills"},
])
def test_missing_identity_does_not_enable_shared_mode(context):
    skill = HarnessSkill.__new__(HarnessSkill)
    spoken = []
    skill.speak_to = lambda source, text, **kw: spoken.append(text)
    source = Message("test", {"utterance": "enable party mode", "lang": "en-US"}, context)
    assert skill.handle_fallback(source)
    assert get_interaction_mode(source) is None
    assert spoken[-1] in RESOURCES.dialog_lines("interaction.mode.unavailable", "en-US")


@pytest.mark.parametrize("value", ["oops", [], {}, float("inf"), None])
def test_invalid_duration_setting_uses_default(monkeypatch, value):
    skill = HarnessSkill.__new__(HarnessSkill)
    monkeypatch.setattr(HarnessSkill, "settings", property(lambda self: {"mode_ttl_seconds": value}))
    assert skill.mode_ttl_seconds == 1800


def test_reading_status_does_not_extend_expiry(monkeypatch):
    from thalovant_skill_interaction_modes import set_interaction_mode
    now = 1000.0
    monkeypatch.setattr("thalovant_skill_interaction_modes.time.monotonic", lambda: now)
    source = utterance_message("what mode are we in")
    assert set_interaction_mode(source, "party", ttl_seconds=10)
    now += 9
    assert get_interaction_mode(source) == "party"
    now += 1
    assert get_interaction_mode(source) is None
