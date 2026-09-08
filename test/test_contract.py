"""The locale tree, entry point and package data, checked the way every
Thalovant skill checks them: `thalovant-skillkit check`."""
from pathlib import Path

from thalovant_skillkit.checks import check_all


def test_the_skill_keeps_its_contracts():
    problems = check_all(Path(__file__).resolve().parents[1])
    assert not problems, "\n".join(problems)
