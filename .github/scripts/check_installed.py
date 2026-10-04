"""Run behavior tests from a clean install, outside the source checkout."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
wheel = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix="interaction-modes-wheel-") as directory:
    work = Path(directory)
    env = work / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(env)], check=True)
    python = env / "bin/python"
    subprocess.run([
        str(python), "-m", "pip", "install", "--pre",
        f"{wheel}[test]", "pytest-timeout",
    ], check=True, cwd=work)
    subprocess.run([
        str(python), "-c",
        "import ovoscope; import thalovant_skill_interaction_modes as skill; "
        "from importlib.metadata import distribution; "
        "d = distribution('thalovant-skill-interaction-modes'); "
        "assert d.metadata['Requires-Python'] == '>=3.10'; "
        "assert any(e.load() is skill.InteractionModesSkill for e in d.entry_points "
        "if e.group == 'ovos.plugin.skill'); "
        "assert 'site-packages' in skill.__file__, skill.__file__",
    ], check=True, cwd=work)
    tests = work / "test"
    tests.mkdir()
    # Source/locale contracts are checked separately against both archives.
    for name in ("conftest.py", "test_interaction_modes.py",
                 "test_multilingual.py", "test_ovoscope.py"):
        shutil.copy2(root / "test" / name, tests / name)
    subprocess.run([str(python), "-m", "pytest", "-q", "--timeout=60", str(tests)],
                   check=True, cwd=work)
