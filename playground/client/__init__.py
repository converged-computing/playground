#!/usr/bin/env python

# Copyright 2022 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import argparse
import os
import sys

import playground
import playground.main.backends as backends
from playground.logger import setup_logger


def get_parser():
    parser = argparse.ArgumentParser(
        description="Playground",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Global Variables
    parser.add_argument(
        "--debug",
        dest="debug",
        help="use verbose logging to debug.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--quiet",
        dest="quiet",
        help="suppress additional output.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--verbose",
        dest="verbose",
        help="print additional solver output (atoms).",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--settings-file",
        dest="settings_file",
        help="custom path to settings file.",
    )

    # On the fly updates to config params
    parser.add_argument(
        "-c",
        dest="config_params",
        help=""""customize a config value on the fly to ADD/SET/REMOVE for a command
playground -c set:key:value <command> <args>
playground -c add:registry:/tmp/registry <command> <args>
playground -c rm:registry:/tmp/registry""",
        action="append",
    )
    parser.add_argument(
        "--version",
        dest="version",
        help="show software version.",
        default=False,
        action="store_true",
    )

    subparsers = parser.add_subparsers(
        help="playground actions",
        title="actions",
        description="actions",
        dest="command",
    )

    # print version and exit
    subparsers.add_parser("version", description="show software version")

    # Local shell with client loaded
    shell = subparsers.add_parser(
        "shell",
        description="shell into a Python session with a client.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    shell.add_argument(
        "--interpreter",
        "-i",
        dest="interpreter",
        help="python interpreter",
        choices=["ipython", "python", "bpython"],
        default="ipython",
    )

    test = subparsers.add_parser(
        "test",
        description="test a playground deployment (if docker/podman will be headless)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    test.add_argument(
        "--sleep",
        "-s",
        help="time to wait after container running to test HTTP endpoint",
        default=5,
        type=int,
    )
    test.add_argument(
        "--http-code",
        dest="http_code",
        help="HTTP code to test for (defaults to 200)",
        default=200,
        type=int,
    )

    config = subparsers.add_parser(
        "config",
        description="update configuration settings. Use set or get to see or set information.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    config.add_argument(
        "--central",
        dest="central",
        help="make edits to the central config file.",
        default=False,
        action="store_true",
    )

    config.add_argument(
        "params",
        nargs="*",
        help="""Set or get a config value, edit the config, add or remove a list variable, or create a user-specific config.
playground config set key value
playground config set key:subkey value
playground config get key
playground config edit
playground config inituser
playground config remove backend aws
playground config add backend aws""",
        type=str,
    )

    listing = subparsers.add_parser(
        "list",
        description="list tutorials available in a tutorial repository.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    show = subparsers.add_parser(
        "show",
        description="show metadata for a tutorial repository.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    deploy = subparsers.add_parser(
        "deploy",
        description="deploy a tutorial repository.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    for command in deploy, test:
        command.add_argument(
            "-o",
            dest="deploy_options",
            help=""""Add deploy options for a backend of choice
playground deploy -o headless:true <args>
""",
            action="append",
        )

    stop = subparsers.add_parser(
        "stop",
        description="stop a tutorial.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    for command in show, deploy, listing, stop, test:
        command.add_argument("repo", help="the tutorial repository to target.")

    show.add_argument(
        "--outfile",
        dest="outfile",
        help="Write repository as json to output file.",
    )

    deploy.add_argument(
        "--env",
        dest="envars",
        help="environment variable key pair key=pair to use during deploy.",
        action="append",
    )
    for command in deploy, stop, show, test:
        command.add_argument(
            "tutorial_name", help="the tutorial name to target (required)"
        )

    for command in deploy, show, listing, shell, stop, test:
        command.add_argument(
            "-b",
            "--backend",
            dest="backend",
            help="the backend to use (defaults to docker)",
            choices=backends.backend_names,
            default="docker",
        )

    return parser


def run():
    parser = get_parser()

    def help(return_code=0):
        version = playground.__version__

        print("\nPlayground Client v%s" % version)
        parser.print_help()
        sys.exit(return_code)

    # If the user didn't provide any arguments, show the full help
    if len(sys.argv) == 1:
        help()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    if args.debug is True:
        os.environ["MESSAGELEVEL"] = "DEBUG"

    # Show the version and exit
    if args.command == "version" or args.version:
        print(playground.__version__)
        sys.exit(0)

    setup_logger(
        quiet=args.quiet,
        debug=args.debug,
    )

    # retrieve subparser (with help) from parser
    helper = None
    subparsers_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    for subparsers_action in subparsers_actions:
        for choice, subparser in subparsers_action.choices.items():
            if choice == args.command:
                helper = subparser
                break

    # Does the user want a shell?
    if args.command == "deploy":
        from .deploy import main
    elif args.command == "config":
        from .config import main
    elif args.command == "list":
        from .listing import main
    elif args.command == "stop":
        from .stop import main
    elif args.command == "show":
        from .show import main
    elif args.command == "test":
        from .test import main

    # Pass on to the correct parser
    return_code = 0
    try:
        main(args=args, parser=parser, extra=extra, subparser=helper)
        sys.exit(return_code)
    except UnboundLocalError:
        return_code = 1

    help(return_code)


if __name__ == "__main__":
    run()
