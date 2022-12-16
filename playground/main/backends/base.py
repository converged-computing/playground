# Copyright 2022 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)


class Backend:
    """
    A base class for a backend
    """

    name = "backend"

    def __init__(self):

        # If we weren't created with settings, add empty
        if not hasattr(self, "settings"):
            from playground.main.settings import Settings

            self.settings = Settings()

    def __str__(self):
        return str(self.__class__.__name__)

    def check_envars(self, tutorial, envars):
        """
        Check envars will ensure required are present.
        """
        import IPython

        IPython.embed()

    def instances(self, *args, **kwargs):
        raise NotImplementedError

    def deploy(self, *args, **kwargs):
        raise NotImplementedError
