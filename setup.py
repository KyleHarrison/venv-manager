from setuptools import find_packages, setup

requirements = ["click", "pyyaml", "virtualenv-api"]

dev_requirements = [
    "black",
    "bumpversion",
    "flake8",
    "isort",
    "pytest",
    "coverage",
    "pytest-cov",
    "radon[flake8]",
    "tox",
]


setup(
    name="venvman",
    version="0.0.1",
    author="Kyle Harrison",
    author_email="kyleharrison94@hotmail.com",
    packages=find_packages(),
    license="LICENSE.md",
    description=("A Python package for managing multiple virtual environments."),
    long_description=open("README.md").read(),
    install_requires=requirements,
    extras_require={"dev": dev_requirements},
    py_modules=["create"],
    entry_points="""
        [console_scripts]
        venvman=venvman.cli:venvman
    """,
)
