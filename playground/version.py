# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

__version__ = "0.0.11"
AUTHOR = "Vanessa Sochat"
EMAIL = "vsoch@users.noreply.github.com"
NAME = "playground-tutorials"
PACKAGE_URL = "https://github.com/converged-computing/playground"
KEYWORDS = "cloud, tutorial, containers"
DESCRIPTION = "the fun cloud wrapper 🍬️ to deploy tutorial containers! 📦️"
LICENSE = "LICENSE"

################################################################################
# Global requirements

# Since we assume wanting Singularity and lmod, we require spython and Jinja2

INSTALL_REQUIRES = (
    ("requests", {"min_version": None}),
    ("ruamel.yaml", {"min_version": None}),
    ("jsonschema", {"min_version": None}),
    ("rich", {"min_version": None}),
    ("requests", {"min_version": None}),
    ("cloud-select-tool", {"min_version": None}),
)

AWS_REQUIRES = (("boto3", {"min_version": None}),)

DOCKER_REQUIRES = (("docker", {"min_version": None}),)

# Prefer discovery clients - more control
GOOGLE_CLOUD_REQUIRES = (
    ("google-auth", {"min_version": None}),
    ("google-api-python-client", {"min_version": None}),
)

TESTS_REQUIRES = (("pytest", {"min_version": "4.6.2"}),)

################################################################################
# Submodule Requirements (versions that include database)

INSTALL_REQUIRES_ALL = (
    INSTALL_REQUIRES
    + GOOGLE_CLOUD_REQUIRES
    + AWS_REQUIRES
    + TESTS_REQUIRES
    + DOCKER_REQUIRES
)
