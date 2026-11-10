"""SPEECH_STYLE paces every reply on a kit that has it, and the skill still loads on one that has not."""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import textwrap

import pytest

import thalovant_skill_interaction_modes as module

LOCALE = pathlib.Path(module.__file__).parent / "locale"


def _skill_class():
    return next(v for v in vars(module).values()
                if isinstance(v, type) and v.__module__ == module.__name__ and "SPEECH_STYLE" in vars(v))


def test_the_style_derives_valid_markup_that_says_the_same_words():
    style = _skill_class().SPEECH_STYLE
    if style is None:
        pytest.skip("skillkit without SpeechStyle: the skill speaks plainly")
    from thalovant_skillkit.ssml import auto_twin, validate

    # Every reply this skill ships today is one short sentence, so the locale files alone would
    # prove nothing; a line a translator makes longer is paced the same way, and must stay valid.
    lines = [("a longer line", "Party mode is on. Back to normal: say stop - or ask for status.")]
    paced = 0
    for dialog in sorted(LOCALE.glob("*/dialog/*.dialog")):
        for line in dialog.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append((dialog, line))
    for dialog, line in lines:
        twin = auto_twin(line, style)
        if twin is None:
            continue
        paced += 1
        assert validate(twin) == [], (dialog, line)
        words = re.sub(r"<[^>]+>", "", twin)
        assert re.sub(r"\s+", "", words) == re.sub(r"\s+", "", line), (dialog, line)
    assert paced > 0


# What skillkit 0.34 and 0.35 added to `thalovant_skillkit.ssml`: a runtime whose loaded kit is older has none.
NEWER = (
    "SpeechStyle", "auto_twin", "cardinal", "ordinal", "fraction", "unit", "currency", "address",
    "interjection", "expletive", "as_date", "as_time", "phoneme", "mark", "prosody", "pitch",
    "whisper", "soft", "compress", "vocal_tract", "breath", "auto_breaths",
)


def test_a_skillkit_without_the_newer_names_still_loads_the_skill_and_speaks_plainly():
    """A hub keeps the skillkit it loaded until its runtime restarts, so the skill meets an old one.

    Run in a process of its own: reloading the skill in the test process would leave two copies of
    its classes behind for every test that follows.
    """
    code = textwrap.dedent(f"""
        import importlib
        import pkgutil
        import thalovant_skillkit
        import thalovant_skillkit.ssml as kit
        for found in pkgutil.iter_modules(thalovant_skillkit.__path__):
            try:
                importlib.import_module("thalovant_skillkit." + found.name)  # the kit's own, loaded whole
            except Exception:
                pass
        for name in {NEWER!r}:
            if hasattr(kit, name):
                delattr(kit, name)
        import {module.__name__} as module
        cls = next(v for v in vars(module).values()
                   if isinstance(v, type) and v.__module__ == module.__name__ and "SPEECH_STYLE" in vars(v))
        assert cls.SPEECH_STYLE is None, cls.SPEECH_STYLE
        print("loaded")
    """)
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300)
    assert done.returncode == 0 and "loaded" in done.stdout, done.stderr[-2000:]


def test_the_style_is_declared_on_a_kit_that_has_it():
    import thalovant_skillkit.ssml as kit_ssml

    if not hasattr(kit_ssml, "SpeechStyle"):
        pytest.skip("this kit lacks it")
    assert _skill_class().SPEECH_STYLE is not None
