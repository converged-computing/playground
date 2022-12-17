# Copyright 2022 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)


class Backend:
    """
    A base class for a backend
    """

    name = "backend"

    def __init__(self, settings=None):

        self._settings = settings

        # If we weren't created with settings, add empty
        if not self._settings:
            from playground.main.settings import Settings

            self._settings = Settings()

    @property
    def settings(self):
        """
        Return cloud specific settings.
        """
        return self._settings.get(self.name, {})

    def __str__(self):
        return str(self.__class__.__name__)

    def instances(self, *args, **kwargs):
        raise NotImplementedError(
            "The instances function is not implemented for this class."
        )

    def deploy(self, *args, **kwargs):
        raise NotImplementedError(
            "The deploy function is not implemented for this class."
        )
