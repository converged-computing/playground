# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

from playground.main.backends.docker import DockerClient


class PodmanClient(DockerClient):
    """
    A Podman backend to deploy a container (e.g., run locally)
    """

    name = "podman"
