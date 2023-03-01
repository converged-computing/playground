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
    """

    name = "docker"

    def __init__(self, **kwargs):
        self.check()
        super(DockerClient, self).__init__()

    def check(self):
        """
        Ensure the client is installed.
        """
        self.cli = shutil.which(self.name)
        if not self.cli:
            raise ValueError(
                f"The executable '{self.name}' is not available on this system."
            )

    def stop(self, tutorial):
        """
        When run in headless mode, we can stop the container by name.
        """
        cmd = [self.cli, "stop", tutorial.uid]
        return utils.run_command(cmd, stream=True)

    def deploy(self, tutorial, envars=None, **kwargs):
        """
        Deploy via a docker container (locally)
        """
        headless = kwargs.get("headless", False) or False
        envars = envars or {}

        # Right now always pull, in future can do check/skip
        res = utils.run_command([self.cli, "pull", tutorial.container], stream=True)
        if res["return_code"] != 0:
            raise ValueError(
                f"Issue pulling container, return code {res['return_code']}"
            )

        # start to assemble command
        if headless:
            cmd = [self.cli, "run", "-d", "--rm", "--name", tutorial.uid]
        else:
            cmd = [self.cli, "run", "-it", "--rm", "--name", tutorial.uid]

        # Add ports and environment variables
        for port in tutorial.container_ports:
            cmd += ["-p", port]
        for key, val in envars.items():
            cmd += ["--env", f"{key}={val}"]

        # Add the remainder of the commands
        cmd += [tutorial.container]
        logger.info(" ".join(cmd))

        # If running headless, wait for the url to be ready
        res = utils.run_command(cmd, stream=not headless)
        if headless:
            self.show_ip_address("127.0.0.1", tutorial)
        return res
