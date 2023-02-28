# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import shutil

import playground.utils as utils
from playground.logger import logger

from ..base import Backend


class DockerClient(Backend):
    """
    A Docker backend to deploy a container (e.g., run locally)

    We allow the client init to proceed given authentication is not
    possible as it can provide data served from a cache, wrapping
    available instances.
    """

    name = "docker"

    def __init__(self, **kwargs):
        self.docker = shutil.which("docker")
        if not self.docker:
            raise ValueError("The executable 'docker' is not available on this system.")
        super(DockerClient, self).__init__()

    def deploy(self, tutorial, envars=None):
        """
        Deploy via a docker container (locally)
        """
        envars = envars or {}

        # Right now always pull, in future can do check/skip
        res = utils.run_command([self.docker, "pull", tutorial.container], stream=True)
        if res["return_code"] != 0:
            raise ValueError(
                f"Issue pulling container, return code {res['return_code']}"
            )

        # start to assemble command
        cmd = [self.docker, "run", "-it", "--rm"]

        # Add ports and environment variables
        for port in tutorial.container_ports:
            cmd += ["-p", port]
        for key, val in envars.items():
            cmd += ["--env", f"{key}={val}"]

        # Add the remainder of the commands
        cmd += [tutorial.container]
        logger.info(" ".join(cmd))
        return utils.run_command(cmd, stream=True)
