#!/usr/bin/python

# Copyright 2022 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import os

import pytest

from .helpers import init_client

here = os.path.dirname(os.path.abspath(__file__))
testdata = os.path.join(here, "testdata")


# We can't easily test AWS/GCP at this point
@pytest.mark.parametrize(
    "backend,tutorial_name",
    [
        ("docker", "radiuss-aws-2022"),
        ("podman", "radiuss-aws-2022"),
    ],
)
def test_playround_test(tmp_path, backend, tutorial_name):
    """
    playground test
    """
    client = init_client(str(tmp_path), backend=backend)
    client.load("rse-ops/flux-tutorials")

    # This also returns the pid if we wanted it
    client.test(tutorial_name)


# We can't easily test AWS/GCP at this point
@pytest.mark.parametrize(
    "backend,filename",
    [
        ("docker", os.path.join(testdata, "tutorial.yaml")),
        ("podman", os.path.join(testdata, "tutorial.yaml")),
    ],
)
def test_playground_filename_test(tmp_path, backend, filename):
    """
    playground test with filename
    """
    client = init_client(str(tmp_path), backend=backend)
    client.load(filename)

    # This also returns the pid if we wanted it
    client.test("local")
