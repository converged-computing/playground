# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import re

import jsonschema
import requests

import playground.main.schemas as schemas
import playground.main.tutorial as tutorials
from playground.logger import logger


class Repository:
    def __init__(self, repo, **kwargs):
        self.tutorials = None
        self.name = None
        self.fullname = None
        self.username = None
        self.vcs = None
        if not self.parse(repo):
            raise ValueError(f"Repository uri {repo} does not correctly parse.")
        if not self.load_tutorials():
            raise ValueError(
                f"Repository uri {repo} does not have valid tutorial metadata."
            )

    def parse(self, repo):
        self.raw = repo
        regexp = re.compile(
            "(?P<prefix>(http|https)://)?(?P<vcs>github[.]com)?(/)?(?P<repository>.*)"
        )

        match = re.match(regexp, repo)
        if not match:
            return False

        # match groups
        items = match.groupdict()

        # Default vcs is GitHub
        self.vcs = items["vcs"] or "github.com"
        self.fullname = items["repository"]

        # Repository must have username and repository
        if self.fullname.count("/") != 1:
            logger.warning(
                "Full repository name should only have one slash to separate org/repo."
            )
            return False

        username, repo = self.fullname.split("/", 1)
        self.username = username
        self.name = repo
        return True

    def load_tutorials(self):
        """
        load and validate tutorial metadata
        """
        tset = tutorials.Tutorials()
        res = requests.get(
            f"https://{self.username}.github.io/{self.name}/api/tutorials.json"
        )
        if res.status_code != 200:
            logger.warning(res.text)
            return False
        metadata = res.json()

        # Validate tutorials on the top level
        if jsonschema.validate(metadata, schema=schemas.tutorials) is not None:
            return False
        for name, tutorial in metadata.items():
            # This shouldn't happen with validation above
            if "tutorial" not in tutorial:
                logger.warning(f"Tutorial {name} is missing tutorial block.")
                continue

            # Validation of further inner content done here
            tset.add_tutorial(name, tutorial)
        self.tutorials = tset
        return True
