from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from ovos_workshop.decorators import intent_handler, skill_api_method
from thalovant_skillkit import SkillResources, context_of, fold_words, standardize, utterances
from thalovant_skillkit.skill import ThalovantFallbackSkill
from thalovant_skillkit.sessions import SessionStateStore

LOCALE_DIR = Path(__file__).parent / "locale"
RESOURCES = SkillResources(LOCALE_DIR)
DEFAULT_MODE_TTL_SECONDS = 30 * 60
FALLBACK_PRIORITY = 91
PARTY_MODE = "party"
SUPPORTED_MODES = {PARTY_MODE}


# Shared by the public helper functions and the voice skill. A bounded store
# prevents visitor churn from retaining unlimited state; elapsed time survives
# wall-clock corrections without extending a child's party session.
_CLIENT_MODES = SessionStateStore[str](
    max_entries=1024, clock=lambda: time.monotonic()
)


@lru_cache(maxsize=128)
def _status_prefixes(lang: str) -> tuple[str, ...]:
    """Keep the existing read-only status question with trailing context."""
    return tuple(
        fold_words(line)
        for candidate in RESOURCES.matching_langs(lang)
        for line in RESOURCES.lines(
            candidate, "", "interaction.mode.status.intent", fallback=False
        )
        if fold_words(line)
    )


def _classify_utterance(utterance: str, lang: str) -> str:
    return _classify_utterance_match(utterance, lang)[0]


def _classify_utterance_match(utterance: str, lang: str) -> tuple[str, str]:
    primary_lang = RESOURCES.lang(lang)
    # SkillKit caches exact phrases across compatible regions. Try English
    # separately so an English command on a French speaker gets an English reply.
    text = fold_words(utterance)
    for candidate in dict.fromkeys((primary_lang, RESOURCES.default_lang)):
        reply_lang = (
            standardize(lang)
            if candidate == primary_lang and RESOURCES.matching_langs(lang)
            else candidate
        )
        for action, intent in (
            ("enable", "party.mode.enable"),
            ("disable", "party.mode.disable"),
            ("status", "interaction.mode.status"),
        ):
            if RESOURCES.matches_literal_intent(utterance, intent, candidate):
                return action, reply_lang
        if any(text.startswith(prefix + " ") for prefix in _status_prefixes(candidate)):
            return "status", reply_lang
    return "", primary_lang


def _scope_from_context(context: dict[str, Any] | None) -> str | None:
    if not isinstance(context, dict):
        return None
    session = context.get("session")
    if isinstance(session, dict):
        site_id = session.get("site_id") or session.get("siteId")
        if isinstance(site_id, str) and site_id.strip() and site_id.strip().lower() not in {"unknown", "default"}:
            return site_id.strip()
        session_id = session.get("session_id") or session.get("sessionId")
        if isinstance(session_id, str) and session_id.strip() and session_id.strip().lower() not in {"unknown", "default"}:
            return session_id.strip()
    for key in ("site_id", "siteId", "client_id", "clientId", "source"):
        value = context.get(key)
        if isinstance(value, str) and value.strip() and value.strip().lower() not in {"unknown", "default", "skills", "audio"}:
            return value.strip()
    return None


def interaction_mode_scope(message: Any) -> str | None:
    return _scope_from_context(context_of(message))


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
    _CLIENT_MODES.set(scope, mode, ttl=max(1, ttl_seconds))
    return True


def get_interaction_mode(message: Any) -> str | None:
    scope = interaction_mode_scope(message)
    if not scope:
        return None
    return _CLIENT_MODES.get(scope)


def clear_interaction_mode(message: Any, mode: str | None = None) -> bool:
    scope = interaction_mode_scope(message)
    if not scope:
        return False
    with _CLIENT_MODES.lock:
        state = _CLIENT_MODES.get(scope)
        if state is None or (mode and state != mode.strip().lower()):
            return False
        del _CLIENT_MODES[scope]
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
        try:
            return max(1, int(self.setting("mode_ttl_seconds") or DEFAULT_MODE_TTL_SECONDS))
        except (TypeError, ValueError, OverflowError):
            return DEFAULT_MODE_TTL_SECONDS

    def _match_message(self, message) -> tuple[str, str]:
        # OVOS supplies normalized and original transcripts. Some normalizers
        # strip Indic/Thai marks, so let SkillKit read every supplied phrasing.
        lang = self.lang_of(message)
        for text in utterances(message):
            action, matched_lang = _classify_utterance_match(text, lang)
            if action:
                return action, matched_lang
        return "", lang

    def can_answer(self, message) -> bool:
        return bool(self._match_message(message)[0])

    def handle_fallback(self, message) -> bool:
        """Apply one explicit mode request and reply to its originating speaker."""
        action, matched_lang = self._match_message(message)
        if not action:
            return False
        self._answer_action(message, action, matched_lang)
        return True

    def _answer_action(self, message, action: str, lang: str):
        if action == "enable":
            if set_interaction_mode(message, PARTY_MODE, ttl_seconds=self.mode_ttl_seconds):
                self.speak_to(message, self.dialog("party.mode.enabled", lang), lang=lang)
                return
            self.speak_to(message, self.dialog("interaction.mode.unavailable", lang), lang=lang)
            return
        if action == "disable":
            if clear_interaction_mode(message, PARTY_MODE):
                self.speak_to(message, self.dialog("party.mode.disabled", lang), lang=lang)
                return
            self.speak_to(message, self.dialog("interaction.mode.normal", lang), lang=lang)
            return

        mode = get_interaction_mode(message)
        if mode == PARTY_MODE:
            self.speak_to(message, self.dialog("party.mode.status", lang), lang=lang)
            return
        self.speak_to(message, self.dialog("interaction.mode.normal", lang), lang=lang)

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
