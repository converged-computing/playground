# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

from playground.logger import logger


def parse_envars(listing):
    """
    Parse envars if we have any
    """
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
