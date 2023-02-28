# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import playground.utils as utils
from playground.logger import logger
from playground.main import Playground


def main(args, parser, extra, subparser):
    """
    playground stop https://github.com/rse-ops/flux-tutorials radiuss-aws-2022
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
    try:
        cli.stop(args.tutorial_name)
    except Exception as e:
        logger.exit(f"Issue with deploy: {e}")
