#!/usr/bin/env python
"""Setup script for GeneNetwork Auth package."""
import glob
from pathlib import Path
from setup_commands import RunTests
from setuptools import setup, find_packages

LONG_DESCRIPTION = """
gn-auth project is the authentication/authorisation server to be used
across all GeneNetwork services.
"""

setup(author="Frederick M. Muriithi",
      author_email="fredmanglis@gmail.com",
      description=(
          "Authentication/Authorisation server for GeneNetwork Services."),
      install_requires=[
          "argon2-cffi>=20.1.0"
          "click"
          "Flask==1.1.2"
          "mypy==0.790"
          "mypy-extensions==0.4.3"
          "mysqlclient==2.0.1"
          "pylint==2.5.3"
          "pymonad"
          "redis==3.5.3"
          "requests==2.25.1"
          "flask-cors==3.0.9"
          "xapian-bindings"
      ],
      include_package_data=True,
      packages=find_packages(
          where=".",
          exclude=(
              "tests",
              "tests.*",
              "setup_commands",
              "setup_commands.*")),
      # `package_data` doesn't seem to work. Use MANIFEST.in instead
      scripts=[],
      license="AGPLV3",
      long_description=LONG_DESCRIPTION,
      long_description_content_type="text/markdown",
      name="gn-auth",
      url="https://github.com/genenetwork/gn-auth",
      version="0.0.1",
      tests_require=["pytest", "hypothesis"],
      cmdclass={
          "run_tests": RunTests ## testing
      })
