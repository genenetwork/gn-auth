#!/usr/bin/env python
"""Setup script for GeneNetwork Auth package."""
from setuptools import setup
from setup_commands import RunTests

long_description = """
GeneNetwork-Auth project is the authentication/authorisation server to be used
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
      scripts=[],
      license="AGPLV3",
      long_description=long_description,
      long_description_content_type="text/markdown",
      name="GeneNetwork-Auth",
      packages=[
          "gn_auth",
          "gn_auth.auth",
          "tests"
      ],
      url="https://github.com/genenetwork/gn-auth",
      version="0.0.0",
      tests_require=["pytest", "hypothesis"],
      cmdclass={
          "run_tests": RunTests ## testing
      })
