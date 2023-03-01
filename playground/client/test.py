# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import time

import requests

import playground.utils as utils
from playground.logger import logger
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

    if args.backend in ["docker", "podman"]:
        args.deploy_options = args.deploy_options or []
        args.deploy_options.append("headless=True")
    options = parse_options(args.deploy_options)

    # This also returns the pid if we wanted it
    logger.c.print("Testing deploy...", style="yellow")
    res = client.deploy(args.tutorial_name, **options)

    logger.c.print("Testing for successful return code...", style="yellow")
    assert res["return_code"] == 0
    time.sleep(args.sleep)
    logger.c.print("Testing for successful HTTP response...", style="yellow")
    response = requests.get("https://127.0.0.1:8000", verify=False)
    assert response.status_code == args.http_code
    logger.c.print("Testing stop...", style="yellow")
    res = client.stop(args.tutorial_name)
    assert res["return_code"] == 0
    logger.c.print("All tests pass!", style="green")
