from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ovos_workshop.decorators import intent_handler, skill_api_method
from thalovant_skillkit import SkillResources, context_of, fold_words
from thalovant_skillkit.skill import ThalovantFallbackSkill

LOCALE_DIR = Path(__file__).parent / "locale"
RESOURCES = SkillResources(LOCALE_DIR)
DEFAULT_MODE_TTL_SECONDS = 30 * 60
FALLBACK_PRIORITY = 91
PARTY_MODE = "party"
SUPPORTED_MODES = {PARTY_MODE}


@dataclass
class _ModeState:
    mode: str
    expires_at: float


_CLIENT_MODES: dict[str, _ModeState] = {}


def _localized_intent_lines(lang: str, filename: str) -> tuple[str, ...]:
    """This language's phrasings of one intent file, then English's.

    Both, rather than the first that exists: an English sentence is understood
    on a French hub too, and always was.
    """
    lines: list[str] = []
    for candidate in RESOURCES.candidate_langs(lang):
        lines.extend(RESOURCES.lines(candidate, "", filename))
    return tuple(lines)


def _matches_intent_phrase(utterance: str, lang: str, filename: str) -> bool:
    text = fold_words(utterance)
    if not text:
        return False
    for phrase in _localized_intent_lines(lang, filename):
        needle = fold_words(phrase)
        if needle and (text == needle or text.startswith(needle + " ")):
            return True
    return False


def _classify_utterance(utterance: str, lang: str) -> str:
    return _classify_utterance_match(utterance, lang)[0]


def _classify_utterance_match(utterance: str, lang: str) -> tuple[str, str]:
    primary_lang = RESOURCES.lang(lang)
    for candidate_lang in RESOURCES.candidate_langs(primary_lang):
        if _matches_intent_phrase(utterance, candidate_lang, "party.mode.enable.intent"):
            return "enable", candidate_lang
        if _matches_intent_phrase(utterance, candidate_lang, "party.mode.disable.intent"):
            return "disable", candidate_lang
        if _matches_intent_phrase(utterance, candidate_lang, "interaction.mode.status.intent"):
            return "status", candidate_lang
    return "", primary_lang


def _scope_from_context(context: dict[str, Any] | None) -> str | None:
    if not isinstance(context, dict):
        return None
    session = context.get("session")
    if isinstance(session, dict):
        site_id = session.get("site_id") or session.get("siteId")
        if isinstance(site_id, str) and site_id.strip() and site_id.strip() != "unknown":
            return site_id.strip()
        session_id = session.get("session_id") or session.get("sessionId")
        if isinstance(session_id, str) and session_id.strip() and session_id.strip() != "default":
            return session_id.strip()
    for key in ("site_id", "siteId", "client_id", "clientId", "source"):
        value = context.get(key)
        if isinstance(value, str) and value.strip() and value.strip() != "unknown":
            return value.strip()
    return None


def interaction_mode_scope(message: Any) -> str | None:
    return _scope_from_context(context_of(message))


def _prune(now: float | None = None) -> None:
    reference = time.time() if now is None else now
    expired = [scope for scope, state in _CLIENT_MODES.items() if state.expires_at <= reference]
    for scope in expired:
        _CLIENT_MODES.pop(scope, None)


def set_interaction_mode(
    message: Any,
    mode: str,
    *,
    ttl_seconds: int = DEFAULT_MODE_TTL_SECONDS,
) -> bool:
    mode = (mode or "").strip().lower()
    if mode not in SUPPORTED_MODES:
        return False
    scope = interaction_mode_scope(message)
    if not scope:
        return False
    _prune()
    _CLIENT_MODES[scope] = _ModeState(mode=mode, expires_at=time.time() + max(1, ttl_seconds))
    return True


def get_interaction_mode(message: Any) -> str | None:
    scope = interaction_mode_scope(message)
    if not scope:
        return None
    _prune()
    state = _CLIENT_MODES.get(scope)
    return state.mode if state else None


def clear_interaction_mode(message: Any, mode: str | None = None) -> bool:
    scope = interaction_mode_scope(message)
    if not scope:
        return False
    _prune()
    state = _CLIENT_MODES.get(scope)
    if state is None:
        return False
    if mode and state.mode != mode.strip().lower():
        return False
    _CLIENT_MODES.pop(scope, None)
    return True


def is_interaction_mode(message: Any, mode: str) -> bool:
    return get_interaction_mode(message) == mode.strip().lower()


def reset_interaction_modes() -> None:
    _CLIENT_MODES.clear()


class InteractionModesSkill(ThalovantFallbackSkill):
    """Voice control for temporary client-scoped interaction modes."""

    #: The module constant, so the rung is written once. The base registers the
    #: fallback at it, and an operator may move it with a `fallback_priority`
    #: setting.
    FALLBACK_PRIORITY = FALLBACK_PRIORITY

    @property
    def mode_ttl_seconds(self) -> int:
        return int(self.setting("mode_ttl_seconds") or DEFAULT_MODE_TTL_SECONDS)

    def can_answer(self, message) -> bool:
        return bool(_classify_utterance(self.utterance(message), self.lang_of(message)))

    def handle_fallback(self, message) -> bool:
        """Kept rather than expressed as `reply`: the answer depends on which of
        three sentences was said, and two of them change the mode as a side
        effect. What is spoken is one line either way."""
        action, matched_lang = _classify_utterance_match(
            self.utterance(message), self.lang_of(message)
        )
        if not action:
            return False
        self._answer_action(message, action, matched_lang)
        return True

    def _answer_action(self, message, action: str, lang: str):
        if action == "enable":
            if set_interaction_mode(message, PARTY_MODE, ttl_seconds=self.mode_ttl_seconds):
                self.speak(self.dialog("party.mode.enabled", lang))
                return
            self.speak(self.dialog("interaction.mode.unavailable", lang))
            return
        if action == "disable":
            if clear_interaction_mode(message, PARTY_MODE):
                self.speak(self.dialog("party.mode.disabled", lang))
                return
            self.speak(self.dialog("interaction.mode.normal", lang))
            return

        mode = get_interaction_mode(message)
        if mode == PARTY_MODE:
            self.speak(self.dialog("party.mode.status", lang))
            return
        self.speak(self.dialog("interaction.mode.normal", lang))

    def _preview_action_reply(
        self,
        utterance: str,
        lang: str,
        context: dict[str, Any] | None,
        *,
        commit: bool,
    ) -> str:
        action, matched_lang = _classify_utterance_match(utterance, lang)

        class _Message:
            pass

        message = _Message()
        message.context = context or {}
        if action == "enable":
            if commit and not set_interaction_mode(
                message,
                PARTY_MODE,
                ttl_seconds=self.mode_ttl_seconds,
            ):
                return self.dialog("interaction.mode.unavailable", matched_lang)
            return self.dialog("party.mode.enabled", matched_lang)
        if action == "disable":
            if commit:
                if clear_interaction_mode(message, PARTY_MODE):
                    return self.dialog("party.mode.disabled", matched_lang)
                return self.dialog("interaction.mode.normal", matched_lang)
            return self.dialog("party.mode.disabled", matched_lang)
        if action == "status":
            mode = get_interaction_mode(message)
            if mode == PARTY_MODE:
                return self.dialog("party.mode.status", matched_lang)
            return self.dialog("interaction.mode.normal", matched_lang)
        return self.dialog("interaction.mode.normal", matched_lang)

    @intent_handler("party.mode.enable.intent")
    def handle_party_mode_enable(self, message):
        self._answer_action(message, "enable", self.lang_of(message))

    @intent_handler("party.mode.disable.intent")
    def handle_party_mode_disable(self, message):
        self._answer_action(message, "disable", self.lang_of(message))

    @intent_handler("interaction.mode.status.intent")
    def handle_interaction_mode_status(self, message):
        self._answer_action(message, "status", self.lang_of(message))

    @skill_api_method
    def preview_mode(self, context: dict[str, Any] | None = None) -> str | None:
        class _Message:
            pass

        message = _Message()
        message.context = context or {}
        return get_interaction_mode(message)

    @skill_api_method
    def preview_reply(
        self,
        utterance: str = "",
        lang: str | None = None,
        context: dict[str, Any] | None = None,
        commit: bool = False,
    ) -> str:
        return self._preview_action_reply(
            utterance or "",
            RESOURCES.lang(lang or self._own_lang()),
            context,
            commit=commit,
        )


def create_skill():
    return InteractionModesSkill()
