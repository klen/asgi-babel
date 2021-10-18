"""Setup the package."""


# Parse requirements
# ------------------
import pkg_resources
import pathlib


def parse_requirements(path: str) -> 'list[str]':
    with pathlib.Path(path).open() as requirements:
        return [str(req) for req in pkg_resources.parse_requirements(requirements)]


# Setup package
# -------------

from setuptools import setup


setup(
    install_requires=parse_requirements('requirements/requirements.txt'),
    extras_require={
        'tests': parse_requirements('requirements/requirements-tests.txt'),
        'build': parse_requirements('requirements/requirements-build.txt'),
        'example': parse_requirements('requirements/requirements-example.txt'),
    },
)

# pylama:ignore=E402,D
