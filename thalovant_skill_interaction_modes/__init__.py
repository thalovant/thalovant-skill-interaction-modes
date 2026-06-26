from __future__ import annotations

import random
import re
import time
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler, skill_api_method
from ovos_workshop.skills.fallback import FallbackSkill

try:
    from ovos_spec_tools import standardize_lang
except ImportError:  # pragma: no cover - compatibility with older OVOS stacks.
    from ovos_utils.lang import standardize_lang_tag as standardize_lang


LOCALE_DIR = Path(__file__).parent / "locale"
DEFAULT_MODE_TTL_SECONDS = 30 * 60
FALLBACK_PRIORITY = 87
PARTY_MODE = "party"
SUPPORTED_MODES = {PARTY_MODE}


@dataclass
class _ModeState:
    mode: str
    expires_at: float


_CLIENT_MODES: dict[str, _ModeState] = {}


def _resource_lang(lang: str | None) -> str:
    normalized = standardize_lang(lang or "en-US")
    if normalized.lower().startswith("fr"):
        return "fr-FR"
    return "en-US"


@lru_cache(maxsize=1)
def _available_langs() -> tuple[str, ...]:
    return tuple(sorted(path.name for path in LOCALE_DIR.iterdir() if path.is_dir()))


def _candidate_langs(lang: str | None) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in (_resource_lang(lang), *_available_langs(), "en-US"):
        if candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return tuple(ordered)


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    without_marks = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", without_marks)).strip()


@lru_cache(maxsize=128)
def _resource_file_lines(resource_lang: str, folder: str, filename: str) -> tuple[str, ...]:
    path = LOCALE_DIR / resource_lang / folder / filename
    if not path.exists():
        return ()
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


@lru_cache(maxsize=128)
def _intent_file_lines(resource_lang: str, filename: str) -> tuple[str, ...]:
    path = LOCALE_DIR / resource_lang / filename
    if not path.exists():
        return ()
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )


def _localized_intent_lines(lang: str, filename: str) -> tuple[str, ...]:
    resource_lang = _resource_lang(lang)
    lines: list[str] = []
    seen: set[str] = set()
    for candidate in (resource_lang, "en-US"):
        if candidate in seen:
            continue
        seen.add(candidate)
        lines.extend(_intent_file_lines(candidate, filename))
    return tuple(lines)


def _message_lang(message: Any, fallback: str) -> str:
    context = getattr(message, "context", {}) or {}
    data = getattr(message, "data", {}) or {}
    session = context.get("session") if isinstance(context, dict) else {}
    if not isinstance(session, dict):
        session = {}
    return _resource_lang(data.get("lang") or context.get("lang") or session.get("lang") or fallback)


def _utterance(message: Any) -> str:
    data = getattr(message, "data", {}) or {}
    utterance = data.get("utterance")
    if isinstance(utterance, str) and utterance.strip():
        return utterance.strip()
    utterances = data.get("utterances")
    if isinstance(utterances, list):
        for candidate in utterances:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return ""


def _matches_intent_phrase(utterance: str, lang: str, filename: str) -> bool:
    text = _fold(utterance)
    if not text:
        return False
    for phrase in _localized_intent_lines(lang, filename):
        needle = _fold(phrase)
        if needle and (text == needle or text.startswith(needle + " ")):
            return True
    return False


def _classify_utterance(utterance: str, lang: str) -> str:
    return _classify_utterance_match(utterance, lang)[0]


def _classify_utterance_match(utterance: str, lang: str) -> tuple[str, str]:
    primary_lang = _resource_lang(lang)
    for candidate_lang in _candidate_langs(primary_lang):
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
    return _scope_from_context(getattr(message, "context", {}) or {})


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


class InteractionModesSkill(FallbackSkill):
    """Voice control for temporary client-scoped interaction modes."""

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(
            network_before_load=False,
            internet_before_load=False,
            gui_before_load=False,
            requires_network=False,
            requires_internet=False,
            requires_gui=False,
            no_network_fallback=True,
            no_internet_fallback=True,
            no_gui_fallback=True,
        )

    @property
    def mode_ttl_seconds(self) -> int:
        return int(self.settings.get("mode_ttl_seconds") or DEFAULT_MODE_TTL_SECONDS)

    def initialize(self):
        self.register_fallback(self._fallback_answer, FALLBACK_PRIORITY)

    def _dialog(self, name: str, lang: str, data: dict | None = None) -> str:
        resource_lang = _resource_lang(lang)
        lines = _resource_file_lines(resource_lang, "dialog", f"{name}.dialog")
        if not lines and resource_lang != "en-US":
            lines = _resource_file_lines("en-US", "dialog", f"{name}.dialog")
        template = random.choice(lines) if lines else name
        return template.format(**(data or {})).replace("\\n", "\n")

    def can_answer(self, message) -> bool:
        lang = _message_lang(message, self.lang)
        return bool(_classify_utterance(_utterance(message), lang))

    def _fallback_answer(self, message) -> bool:
        lang = _message_lang(message, self.lang)
        action, matched_lang = _classify_utterance_match(_utterance(message), lang)
        if not action:
            return False
        self._answer_action(message, action, matched_lang)
        return True

    def _answer_action(self, message, action: str, lang: str):
        if action == "enable":
            if set_interaction_mode(message, PARTY_MODE, ttl_seconds=self.mode_ttl_seconds):
                self.speak(self._dialog("party.mode.enabled", lang))
                return
            self.speak(self._dialog("interaction.mode.unavailable", lang))
            return
        if action == "disable":
            if clear_interaction_mode(message, PARTY_MODE):
                self.speak(self._dialog("party.mode.disabled", lang))
                return
            self.speak(self._dialog("interaction.mode.normal", lang))
            return

        mode = get_interaction_mode(message)
        if mode == PARTY_MODE:
            self.speak(self._dialog("party.mode.status", lang))
            return
        self.speak(self._dialog("interaction.mode.normal", lang))

    @intent_handler("party.mode.enable.intent")
    def handle_party_mode_enable(self, message):
        lang = _message_lang(message, self.lang)
        self._answer_action(message, "enable", lang)

    @intent_handler("party.mode.disable.intent")
    def handle_party_mode_disable(self, message):
        lang = _message_lang(message, self.lang)
        self._answer_action(message, "disable", lang)

    @intent_handler("interaction.mode.status.intent")
    def handle_interaction_mode_status(self, message):
        lang = _message_lang(message, self.lang)
        self._answer_action(message, "status", lang)

    @skill_api_method
    def preview_mode(self, context: dict[str, Any] | None = None) -> str | None:
        class _Message:
            pass

        message = _Message()
        message.context = context or {}
        return get_interaction_mode(message)


def create_skill():
    return InteractionModesSkill()
