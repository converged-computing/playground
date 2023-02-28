# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import json

from rich import print_json

import playground.utils as utils
from playground.main import Playground


def main(args, parser, extra, subparser):
    """
    playground show https://github.com/rse-ops/flux-tutorials
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
    if not args.tutorial_name:
        tutorials = cli.get_tutorials()
    else:
        tutorials = cli.get_tutorial(args.tutorial_name)

    # Print instances to a table
    if args.outfile:
        utils.write_json(tutorials, args.outfile, cls=tutorials.Encoder)
    else:
        print_json(json.dumps(tutorials, cls=tutorials.Encoder, indent=4))
