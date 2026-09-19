from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]
LOCALE_ROOT = next(REPOSITORY_ROOT.glob("thalovant_skill_*/locale"))


def test_supported_locales_have_complete_resource_contracts():
    # One policy for regional inheritance, placeholders and metadata across the fleet.
    from thalovant_skillkit.checks import check_locale_contract

    assert check_locale_contract(REPOSITORY_ROOT) == []
