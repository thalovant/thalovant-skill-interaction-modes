#!/usr/bin/env python3
from __future__ import annotations

import os
from os import path, walk

from setuptools import setup

URL = "https://github.com/thalovant/thalovant-skill-interaction-modes"
SKILL_CLAZZ = "InteractionModesSkill"
PYPI_NAME = "thalovant-skill-interaction-modes"
SKILL_PKG = "thalovant_skill_interaction_modes"
SKILL_AUTHOR = "thalovant"
SKILL_NAME = "thalovant-skill-interaction-modes"
PLUGIN_ENTRY_POINT = f"{SKILL_NAME}.{SKILL_AUTHOR}={SKILL_PKG}:{SKILL_CLAZZ}"


def find_resource_files():
    base_dir = path.join(os.path.dirname(__file__), SKILL_PKG)
    package_data = ["*.json"]
    for res in ("locale",):
        res_dir = path.join(base_dir, res)
        if path.isdir(res_dir):
            for directory, _, files in walk(res_dir):
                if files:
                    relative_dir = directory.replace(base_dir + os.sep, "")
                    package_data.append(path.join(relative_dir, "*"))
    return package_data


def get_version():
    version_ns = {}
    version_file = path.join(path.dirname(__file__), SKILL_PKG, "version.py")
    with open(version_file, encoding="utf-8") as handle:
        exec(handle.read(), version_ns)
    return version_ns["__version__"]


with open(path.join(path.abspath(path.dirname(__file__)), "README.md"), encoding="utf-8") as handle:
    long_description = handle.read()


setup(
    name=PYPI_NAME,
    version=get_version(),
    description="Temporary client-scoped interaction modes for Thalovant hubs.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=URL,
    author=SKILL_AUTHOR,
    license="Apache-2.0",
    packages=[SKILL_PKG],
    package_data={SKILL_PKG: find_resource_files()},
    include_package_data=True,
    install_requires=[
        line.strip()
        for line in open("requirements.txt", encoding="utf-8")
        if line.strip() and not line.startswith("#")
    ],
    keywords="ovos skill plugin thalovant hivemind interaction modes",
    entry_points={"ovos.plugin.skill": PLUGIN_ENTRY_POINT},
)
