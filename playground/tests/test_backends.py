#!/usr/bin/python

# Copyright 2022 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import time

import jsonschema
import pytest
import requests

import playground.main.schemas as schemas

from .helpers import init_client


# We can't easily test AWS/GCP at this point
@pytest.mark.parametrize(
    "backend,tutorial_name",
    [
        ("docker", "radiuss-aws-2022"),
        ("podman", "radiuss-aws-2022"),
    ],
)
def test_instance_command(tmp_path, backend, tutorial_name):
    """
    Test backends
    """
    client = init_client(str(tmp_path), backend=backend)

    # Listing without a tutorial doesn't work
    with pytest.raises(SystemExit):
        client.list()
        client.get_tutorials()

    assert client.backend.name == backend

    client.load("rse-ops/flux-tutorials")
    assert client.repo is not None
    client.list()
    tutorials = client.get_tutorials()
    assert tutorials.tutorials
    assert tutorial_name in tutorials.tutorials

    tutorial = client.get_tutorial(tutorial_name)
    assert jsonschema.validate(tutorial.data, schemas.tutorials) is None

    # This also returns the pid if we wanted it
    client.deploy(tutorial_name, headless=True)
    time.sleep(10)
    response = requests.get("https://127.0.0.1:8000", verify=False)
    assert response.status_code == 200
    client.stop(tutorial_name)
