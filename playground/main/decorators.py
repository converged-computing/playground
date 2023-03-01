# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

from functools import partial, update_wrapper

from playground.logger import logger


class Decorator:
    """
    Shared parent decorator class
    """

    def __init__(self, func, attempts=5, timeout=2):
        update_wrapper(self, func)
        self.func = func

    def __get__(self, obj, objtype):
        return partial(self.__call__, obj)


class repository(Decorator):
    """
    Require that the client has a self.repo
    """

    def __init__(self, func):
        update_wrapper(self, func)
        self.func = func

    def __call__(self, cls, *args, **kwargs):
        if not cls.repo:
            logger.exit("Use load() to load a repository.")
        return self.func(cls, *args, **kwargs)
