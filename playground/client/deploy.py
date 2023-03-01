# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import playground.utils as utils
from playground.logger import logger
from playground.main import Playground


def parse_envars(listing):
    # Parse envars if we have any
    envars = {}
    if not listing:
        return
    for envar in listing:
        if "=" not in envar:
            logger.exit(
                f"Incorrectly formatted environment variable: {envar}, missing '='"
            )
        key, value = envar.split("=", 1)
        envars[key] = value.strip()
    return envars


def parse_options(options):
    """
    Parse extra deploy options provided with -o
    """
    opts = {}
    if not options:
        return opts
    for key, value in parse_envars(options).items():
        if isinstance(value, str) and value.lower() in ["t", "true", "yes"]:
            value = True
        if isinstance(value, str) and value.lower() in ["f", "false", "no"]:
            value = False
        if isinstance(value, str) and value.lower() in ["none", "null"]:
            value = None
        opts[key] = value
    return opts


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
