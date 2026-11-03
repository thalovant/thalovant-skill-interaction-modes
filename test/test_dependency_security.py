"""Guard the installed skill's reviewed filelock dependency and lock behavior."""
import json
import sys
from importlib.metadata import distribution, requires, version
from pathlib import Path

import pytest
from filelock import FileLock, Timeout
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10: the same parser, shipped as tomli.
    import tomli as tomllib

PACKAGE = "thalovant-skill-interaction-modes"
ROOT = Path(__file__).resolve().parents[1]
# filelock up to 4.2.0 is inside published advisory ranges; 4.2.1 needs Python 3.11.
PATCHED = SpecifierSet(">=4.2.1,<5")
LEGACY_PIN = SpecifierSet("==3.20.3")
COMBO_URL = (
    "https://github.com/goldyfruit/combo-lock/archive/"
    "3aa5c729171ab161e54623c59ca8b41e3451c5f5.tar.gz"
    "#sha256=e653deca0dead17177ad141026881899889e8b5c0be5884ebef098d266dc70a7"
)
ON_PATCHED_PYTHON = sys.version_info >= (3, 11)


def _filelock_requirements(entries: list[str]) -> list[Requirement]:
    """Return the filelock requirements among requirement-file or metadata lines."""
    requirements = [Requirement(line) for line in entries
                    if line.strip() and not line.lstrip().startswith(("#", "-"))]
    return [item for item in requirements if item.name == "filelock"]


def _assert_split_pin(locks: list[Requirement]) -> None:
    """3.10 keeps the least-affected 3.x release; 3.11+ requires the fixed 4.x line."""
    by_spec = {str(item.specifier): item for item in locks}
    assert set(by_spec) == {str(LEGACY_PIN), str(PATCHED)}
    legacy, patched = by_spec[str(LEGACY_PIN)], by_spec[str(PATCHED)]
    assert legacy.marker is not None and patched.marker is not None
    for python, expect_legacy in (("3.10", True), ("3.11", False), ("3.14", False)):
        env = {"python_version": python, "python_full_version": f"{python}.0"}
        assert legacy.marker.evaluate(env) is expect_legacy
        assert patched.marker.evaluate(env) is not expect_legacy


def test_installed_metadata_pins_reviewed_filelock() -> None:
    """The published dependency must constrain resolution, not just the scanner."""
    _assert_split_pin(_filelock_requirements(requires(PACKAGE) or []))
    installed = Version(version("filelock"))
    if ON_PATCHED_PYTHON:
        assert installed in PATCHED
    else:
        assert installed in LEGACY_PIN


def test_requirements_install_uses_same_pin() -> None:
    """The requirements install route must agree with package metadata."""
    lines = (ROOT / "requirements.txt").read_text().splitlines()
    _assert_split_pin(_filelock_requirements(lines))


def test_uv_and_pip_installs_use_the_reviewed_combo_lock() -> None:
    """Both install routes name the same SHA-256 pinned combo-lock build for 3.11+."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    overrides = [Requirement(item) for item in project["tool"]["uv"]["override-dependencies"]]
    ci = (ROOT / ".github/ci/runtime-security-requirements.txt").read_text().splitlines()
    pinned = [Requirement(line) for line in ci if line.strip() and not line.startswith("#")]
    for entries in (overrides, pinned):
        combo = [item for item in entries if item.name == "combo-lock" and item.url]
        assert len(combo) == 1
        assert combo[0].url == COMBO_URL
        assert str(combo[0].marker) == 'python_version >= "3.11"'
    assert any(item.name == "filelock" and item.specifier == PATCHED for item in pinned)
    # An override replaces every requirement on the package, so 3.10 keeps the
    # published combo-lock through its own entry instead of losing it.
    legacy = [item for item in overrides if item.name == "combo-lock" and not item.url]
    assert len(legacy) == 1 and str(legacy[0].marker) == 'python_version < "3.11"'


@pytest.mark.skipif(not ON_PATCHED_PYTHON, reason="the reviewed build is only used on 3.11+")
def test_installed_combo_lock_is_the_reviewed_build() -> None:
    """CI must test against the combo-lock build hubs run, not the published one."""
    combo = distribution("combo-lock")
    assert combo.version == "0.3.1+thalovant.1"
    origin = json.loads(combo.read_text("direct_url.json") or "{}")
    assert origin.get("url") == COMBO_URL.split("#", 1)[0]


def test_classic_filelock_exclusion_and_reuse(tmp_path: Path) -> None:
    """The selected dependency still excludes a competing lock and can reopen."""
    path = str(tmp_path / "skill.lock")
    first, second = FileLock(path), FileLock(path)
    with first:
        with pytest.raises(Timeout):
            second.acquire(timeout=0)
    with second.acquire(timeout=0):
        assert second.is_locked
