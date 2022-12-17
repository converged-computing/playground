# Copyright 2022 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import json

import jsonschema

import playground.main.schemas as schemas
import playground.main.templates as templates
import playground.utils as utils
from playground.logger import logger


class TutorialEncoder(json.JSONEncoder):
    """
    Json dump a tutorial via the _config attribute
    """

    def default(self, o):
        return o._config


class TutorialsEncoder(json.JSONEncoder):
    """
    Json dump a tutorial via the _config attribute
    """

    def default(self, o):
        tutorials = {}
        for name, tutorial in o.tutorials.items():
            tutorials[name] = tutorial._config
        return tutorials


class Tutorials:
    """
    A grouping of tutorials.
    """

    Encoder = TutorialsEncoder

    def __init__(self):
        self.tutorials = {}

    def __iter__(self):
        """
        Generate a list of tutorial attributes.
        """
        for _, tutorial in self.tutorials.items():
            yield tutorial

    def add_tutorial(self, name, tutorial):
        """
        add to the named lookup of tutorials
        """
        try:
            new_tutorial = Tutorial(name, tutorial)
        except Exception as e:
            logger.warning(f"Tutorial {name} is not valid, skipping: {e}")
            return
        self.tutorials[name] = new_tutorial

    def get(self, name):
        """
        Get a tutorial by name
        """
        return self.tutorials.get(name)


class Tutorial:

    Encoder = TutorialEncoder

    def __init__(self, name, metadata):
        self._config = metadata
        self.name = name
        self.validate()

    @property
    def slug(self):
        return utils.slugify(self.title)

    def prepare_startup_script(self, envars=None):
        """
        Prepare the script to launch the tutorial via the instance.
        """
        envars = envars or {}
        command = f"sudo docker pull {self.container}\nsudo docker run -it --rm"
        hidden = command
        for port in self.container_ports:
            command += f" -p {port}"
            hidden += f" -p {port}"

        # Add envars
        for key, value in envars.items():
            command += f" --env {key}={value}"
            hidden += f' --env {key}={len(value)*"*"}'

        command += " " + self.container
        hidden += " " + self.container
        logger.info(hidden)
        return templates.docker_template + "\n" + command

    def validate(self):
        """
        Validate the individual tutorial (and details about properties)
        """
        if (
            jsonschema.validate(self._config, schema=schemas.tutorial_properties)
            is not None
        ):
            raise ValueError(f"Tutorial {self.name} is not valid")
        # Ensure ports parse to two ints
        for portset in self.container_ports:
            if ":" not in portset:
                raise ValueError(
                    f'Port set {portset} is missing ":" separator, and is not valid.'
                )
            for port in portset.split(":"):
                try:
                    int(port)
                except ValueError:
                    raise ValueError(
                        f"Port {port} does not correctly convert to an integer and is not valid."
                    )

    def __iter__(self):
        """
        Generate a list of tutorial attributes.
        """
        # prepare a list item for each attribute
        items = [
            {"attribute": "name", "value": self.name},
            {
                "attribute": "project",
                "value": self.project,
            },
            {
                "attribute": "title",
                "value": self.title,
            },
            {
                "attribute": "notebooks",
                "value": json.dumps(self.notebooks),
            },
            {"attribute": "container", "value": self.container},
        ]
        ports = self.container_ports
        env = self.container_env
        if env:
            items.append(
                {"attribute": "container environment", "value": json.dumps(env)}
            )
        if ports:
            items.append({"attribute": "container ports", "value": json.dumps(ports)})
        for item in items:
            yield item

    # Exposed attributes
    @property
    def data(self):
        return self._config.get("tutorial") or {}

    @property
    def title(self):
        return self.data["title"]

    @property
    def container(self):
        return self.data["container"]["name"]

    @property
    def container_env(self):
        return self.data["container"].get("env")

    @property
    def container_ports(self):
        return self.data["container"].get("ports") or []

    @property
    def notebooks(self):
        return self.data["notebooks"]

    @property
    def project(self):
        return self.data["project"]["github"]
