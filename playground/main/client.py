# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import playground.main.backends as backends
import playground.main.repository as repository
from playground.logger import logger

from .settings import Settings


class Playground:
    """
    A playground is a tutorial repository + backend
    """

    def __init__(self, repo, backend="docker", **kwargs):
        validate = kwargs.get("validate", True)
        self.quiet = kwargs.get("quiet", False)
        self.settings = Settings(kwargs.get("settings_file"), validate)
        self.repo = repository.Repository(repo)
        self.backend = backends.get_backend(backend)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[playground-client]"

    def list(self):
        """
        List tutorials in a playground
        """
        for tutorial in self.repo.tutorials:
            print("🍓 %s\n" % tutorial.name)

    def instances(self):
        """
        List running instances on the backend
        """
        return self.backend.instances()

    def get_tutorial(self, name):
        """
        Show complete repositorty metadata
        """
        tutorial = self.repo.tutorials.get(name)
        if not tutorial:
            logger.warning(f'👀 The tutorial "{name}" is not known!')
            return
        return tutorial

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

    def deploy(self, name, envars=None):
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
        return self.backend(settings=self.settings).deploy(tutorial, envars)

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
