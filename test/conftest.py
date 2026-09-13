
from thalovant_skillkit.testing_ovos import isolated_xdg


def pytest_configure(config):
    environment = isolated_xdg()
    environment.__enter__()
    config.add_cleanup(lambda: environment.__exit__(None, None, None))
