# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import playground.utils
from playground.main import Client


def main(args, parser, extra, subparser):
    playground.utils.ensure_no_extra(extra)
    lookup = {"ipython": ipython, "python": python, "bpython": bpython}
    shells = ["ipython", "python", "bpython"]

    # The default shell determined by the command line client
    shell = args.interpreter
    if shell is not None:
        shell = shell.lower()
        if shell in lookup:
            try:
                return lookup[shell](args)
            except ImportError:
                pass

    # Otherwise present order of liklihood to have on system
    for shell in shells:
        try:
            return lookup[shell](args)
        except ImportError:
            pass


def create_client(args):
    cli = Client(
        quiet=args.quiet,
        settings_file=args.settings_file,
        cache_dir=args.cache_dir,
    )

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)
    return cli


def ipython(args):
    """
    Generate an IPython shell with the client.
    """
    client = create_client(args)  # noqa
    from IPython import embed

    embed()


def bpython(args):
    """
    Generate an bpython shell with the client.
    """
    import bpython

    client = create_client(args)
    bpython.embed(locals_={"client": client})


def python(args):
    """
    Generate an python shell with the client.
    """
    import code

    client = create_client(args)
    code.interact(local={"client": client})
