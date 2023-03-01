# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import time

import requests

import playground.main.backends as backends
import playground.main.decorators as decorators
import playground.main.repository as repository
from playground.logger import logger

from .settings import Settings


class Playground:
    """
    A playground is a tutorial repository + backend
    """

    def __init__(self, repo=None, backend="docker", **kwargs):
        validate = kwargs.get("validate", True)
        self.quiet = kwargs.get("quiet", False)
        self.settings = Settings(kwargs.get("settings_file"), validate)
        self.repo = None
        if repo is not None:
            self.repo = repository.Repository(repo)
        self.backend = backends.get_backend(backend)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[playground-client]"

    @decorators.repository
    def list(self):
        """
        List tutorials in a playground
        """
        for tutorial in self.repo.tutorials:
            print("🍓 %s\n" % tutorial.name)

    def load(self, repo):
        """
        Load a repository
        """
        self.repo = repository.Repository(repo)

    def instances(self):
        """
        List running instances on the backend
        """
        return self.backend.instances()

    @decorators.repository
    def test(self, name, sleep=5, http_code=200, **options):
        """
        Test a named tutorial.
        """
        if self.backend.name in ["docker", "podman"]:
            options["headless"] = True

        # This also returns the pid if we wanted it
        logger.c.print("Testing deploy...", style="yellow")
        res = self.deploy(name, **options)
        logger.c.print("Testing for successful return code...", style="yellow")
        assert res["return_code"] == 0
        time.sleep(sleep)
        logger.c.print("Testing for successful HTTP response...", style="yellow")
        response = requests.get("https://127.0.0.1:8000", verify=False)
        assert response.status_code == http_code
        logger.c.print("Testing stop...", style="yellow")
        res = self.stop(name)
        assert res["return_code"] == 0
        logger.c.print("All tests pass!", style="green")

    @decorators.repository
    def get_tutorial(self, name):
        """
        Show complete repositorty metadata
        """
        tutorial = self.repo.tutorials.get(name)
        if not tutorial:
            logger.warning(f'👀 The tutorial "{name}" is not known!')
            return
        return tutorial

    @decorators.repository
    def get_tutorials(self):
        """
        Courtesy function to return a tutorial.
        """
        return self.repo.tutorials

    def check_envars(self, tutorial, envars):
        """
        Ensure that any required envars are provided.
        """
        for envar in tutorial.container_env:
            if envar["optional"] is False and envar["name"] not in envars:
                raise ValueError(
                    f"Environment variable {envar['name']} is required but not present. Add with --env"
                )

    def deploy(self, name, envars=None, **kwargs):
        """
        Deploy a playground
        """
        if not self.backend:
            raise ValueError("A backend is required to deploy a tutorial to.")
        envars = envars or {}
        tutorial = self.get_tutorial(name)
        if not tutorial:
            logger.error(f"There is no tutorial found named {name} for {self.repo}")
            return
        self.check_envars(tutorial, envars)
        return self.backend(settings=self.settings).deploy(tutorial, envars, **kwargs)

    def stop(self, name):
        """
        Stop a tutorial and clean up.
        """
        if not self.backend:
            raise ValueError("A backend is required to deploy a tutorial to.")
        tutorial = self.get_tutorial(name)
        if not tutorial:
            logger.error(f"There is no tutorial found named {name} for {self.repo}")
            return
        return self.backend(settings=self.settings).stop(tutorial)
