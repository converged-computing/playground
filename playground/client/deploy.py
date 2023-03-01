# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import playground.utils as utils
from playground.logger import logger
from playground.main import Playground

from .helpers import parse_envars, parse_options


def main(args, parser, extra, subparser):
    """
    playground deploy https://github.com/rse-ops/flux-tutorials radiuss-aws-2022
    """
    utils.ensure_no_extra(extra)

    cli = Playground(
        args.repo,
        quiet=args.quiet,
        settings_file=args.settings_file,
        backend=args.backend,
    )

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)

    # Parse envars if we have any
    envars = parse_envars(args.envars)

    # And options
    options = parse_options(args.deploy_options)

    try:
        cli.deploy(args.tutorial_name, envars, **options)
    except Exception as e:
        logger.exit(f"Issue with deploy: {e}")
