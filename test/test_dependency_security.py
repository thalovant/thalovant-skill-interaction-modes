"""Guard the installed skill's reviewed filelock dependency and lock behavior."""
from importlib.metadata import requires, version
from pathlib import Path

import pytest
from filelock import FileLock, Timeout
from packaging.requirements import Requirement


PACKAGE = "thalovant-skill-interaction-modes"


def test_installed_metadata_pins_reviewed_filelock() -> None:
    """The published dependency must constrain resolution, not just the scanner."""
    dependencies = [Requirement(item) for item in requires(PACKAGE) or []]
    matches = [item for item in dependencies if item.name == "filelock"]
    assert len(matches) == 1
    assert str(matches[0].specifier) == "==3.20.3"
    assert version("filelock") == "3.20.3"


def test_requirements_install_uses_same_pin() -> None:
    """The requirements install route must agree with package metadata."""
    lines = (Path(__file__).resolve().parents[1] / "requirements.txt").read_text().splitlines()
    assert "filelock==3.20.3" in lines


def test_classic_filelock_exclusion_and_reuse(tmp_path: Path) -> None:
    """The selected dependency still excludes a competing lock and can reopen."""
    path = str(tmp_path / "skill.lock")
    first, second = FileLock(path), FileLock(path)
    with first:
        with pytest.raises(Timeout):
            second.acquire(timeout=0)
    with second.acquire(timeout=0):
        assert second.is_locked
