import json
import re
from collections import Counter
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]
LOCALE_ROOT = next(REPOSITORY_ROOT.glob("thalovant_skill_*/locale"))
PLACEHOLDER = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}|<[A-Za-z_][A-Za-z0-9_.-]*>")
TECHNICAL_SKILL_KEYS = {
    "author",
    "icon",
    "images",
    "license",
    "package_name",
    "pip_spec",
    "skill_id",
    "source",
    "tags",
    "version",
}


def _resources(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


def _placeholders(path: Path) -> Counter[str]:
    return Counter(PLACEHOLDER.findall(path.read_text(encoding="utf-8")))


def test_supported_locales_have_complete_resource_contracts():
    supported = set(json.loads((LOCALE_ROOT / "supported.json").read_text())["locales"])
    assert supported <= {path.name for path in LOCALE_ROOT.iterdir() if path.is_dir()}

    source_root = LOCALE_ROOT / "en-US"
    source_resources = _resources(source_root)
    for locale in supported:
        target_root = LOCALE_ROOT / locale
        assert source_resources <= _resources(target_root), locale
        for relative in source_resources:
            source = source_root / relative
            target = target_root / relative
            if locale != "fr-FR":
                assert _placeholders(target) == _placeholders(source), f"{locale}: {relative}"
            if relative.suffix == ".json":
                json.loads(target.read_text(encoding="utf-8"))
            elif relative.suffix == ".rx":
                for pattern in target.read_text(encoding="utf-8").splitlines():
                    if pattern.strip() and not pattern.lstrip().startswith("#"):
                        re.compile(pattern)

        skill_metadata = source_root / "skill.json"
        if skill_metadata.exists():
            source_data = json.loads(skill_metadata.read_text(encoding="utf-8"))
            target_data = json.loads((target_root / "skill.json").read_text(encoding="utf-8"))
            for key in TECHNICAL_SKILL_KEYS & source_data.keys():
                if key in target_data:
                    assert target_data[key] == source_data[key], f"{locale}: skill.json:{key}"
