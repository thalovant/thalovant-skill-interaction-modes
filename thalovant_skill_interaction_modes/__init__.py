from __future__ import annotations

import random
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.decorators import intent_handler, skill_api_method
from ovos_workshop.skills import OVOSSkill

try:
    from ovos_spec_tools import standardize_lang
except ImportError:  # pragma: no cover - compatibility with older OVOS stacks.
    from ovos_utils.lang import standardize_lang_tag as standardize_lang


LOCALE_DIR = Path(__file__).parent / "locale"
DEFAULT_MODE_TTL_SECONDS = 30 * 60
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


def _message_lang(message: Any, fallback: str) -> str:
    context = getattr(message, "context", {}) or {}
    return _resource_lang(context.get("lang") or fallback)


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


class InteractionModesSkill(OVOSSkill):
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

    def _dialog(self, name: str, lang: str, data: dict | None = None) -> str:
        resource_lang = _resource_lang(lang)
        lines = _resource_file_lines(resource_lang, "dialog", f"{name}.dialog")
        if not lines and resource_lang != "en-US":
            lines = _resource_file_lines("en-US", "dialog", f"{name}.dialog")
        template = random.choice(lines) if lines else name
        return template.format(**(data or {})).replace("\\n", "\n")

    @intent_handler("party.mode.enable.intent")
    def handle_party_mode_enable(self, message):
        lang = _message_lang(message, self.lang)
        if set_interaction_mode(message, PARTY_MODE, ttl_seconds=self.mode_ttl_seconds):
            self.speak(self._dialog("party.mode.enabled", lang))
            return
        self.speak(self._dialog("interaction.mode.unavailable", lang))

    @intent_handler("party.mode.disable.intent")
    def handle_party_mode_disable(self, message):
        lang = _message_lang(message, self.lang)
        if clear_interaction_mode(message, PARTY_MODE):
            self.speak(self._dialog("party.mode.disabled", lang))
            return
        self.speak(self._dialog("interaction.mode.normal", lang))

    @intent_handler("interaction.mode.status.intent")
    def handle_interaction_mode_status(self, message):
        lang = _message_lang(message, self.lang)
        mode = get_interaction_mode(message)
        if mode == PARTY_MODE:
            self.speak(self._dialog("party.mode.status", lang))
            return
        self.speak(self._dialog("interaction.mode.normal", lang))

    @skill_api_method
    def preview_mode(self, context: dict[str, Any] | None = None) -> str | None:
        class _Message:
            pass

        message = _Message()
        message.context = context or {}
        return get_interaction_mode(message)


def create_skill():
    return InteractionModesSkill()
