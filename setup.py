#!/usr/bin/env python
"""Setup script for GeneNetwork Auth package."""
import glob
from pathlib import Path
from setuptools import setup
from setup_commands import RunTests

LONG_DESCRIPTION = """
gn-auth project is the authentication/authorisation server to be used
across all GeneNetwork services.
"""

def get_packages(dir_path):
    "get package relative to name of directory"
    dir_name = Path(dir_path).absolute().name
    return list(".".join(path) for path in
                (path[0:-1] for path in
                 (path.split("/") for path in
                  glob.glob(f"{dir_name}/**/__init__.py", recursive=True))))

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
      scripts=[],
      license="AGPLV3",
      long_description=LONG_DESCRIPTION,
      long_description_content_type="text/markdown",
      name="gn-auth",
      packages = get_packages("./gn_auth"),
      url="https://github.com/genenetwork/gn-auth",
      version="0.0.1",
      tests_require=["pytest", "hypothesis"],
      cmdclass={
          "run_tests": RunTests ## testing
      })
