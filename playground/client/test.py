# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import playground.utils as utils
from playground.main import Playground

from .helpers import parse_options


def main(args, parser, extra, subparser):
    """
    playground deploy https://github.com/rse-ops/flux-tutorials radiuss-aws-2022
    """
    utils.ensure_no_extra(extra)

    client = Playground(
        args.repo,
        quiet=args.quiet,
        settings_file=args.settings_file,
        backend=args.backend,
    )
    options = parse_options(args.deploy_options)

    # Run the test
    client.test(
        args.tutorial_name, sleep=args.sleep, http_code=args.http_code, **options
    )
