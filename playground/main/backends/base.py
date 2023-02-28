# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import time

import requests
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from playground.logger import logger

# Even self signed certificates will issue a warning with verify=False
requests.packages.urllib3.disable_warnings()


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

    def wait_until_available(
        self, url, sleep=2, spin=None, text="Waiting for tutorial to be ready..."
    ):
        """
        Wait until a URL is available, updating the status message.
        """
        # Wait until the page does not 404
        spin = Spinner("dots", text=Text(text, style="green"))

        # Show a spinner until ready
        with Live(spin, refresh_per_second=20):
            self._wait_until_available(url, spin=spin, sleep=sleep)

    def _wait_until_available(self, url, sleep=2, spin=None):
        """
        Wait until an ip address returns a non-404 response.
        """
        ready = False

        def update_message(text):
            if spin:
                spin.update(text=text, style="green")
            else:
                logger.debug(text)

        while not ready:
            # Second round of tries won't work until instance service is running
            try:
                # We can't verify because even self signed are not good enough!
                response = requests.get(url, verify=False)
                if response.status_code == 404:
                    update_message(
                        f"{url} is not ready yet: response code {response.status_code}. Sleeping {sleep} seconds"
                    )
                    time.sleep(sleep)
                    sleep = sleep + 2
                elif response.status_code != 404:
                    update_message(
                        f"{url} is ready: response code {response.status_code}"
                    )
                    ready = True
                    break

            # First tries will just fail
            except Exception:
                update_message(f"{url} is not ready yet. Sleeping {sleep} seconds")
                time.sleep(sleep)
                sleep = sleep + 2

    def show_ip_address(self, url, tutorial):
        """
        Show the ip address and warn the user things take a bit to start up.
        """
        prefix = "https://" if tutorial.container_https else "http://"
        url = f"{prefix}{url}"
        if tutorial.expose_port:
            url = f"{url}:{tutorial.expose_port}"

        self.wait_until_available(url)
        logger.c.print(f"Ready: {url}")

    def ensure_firewall(self, tutorial):
        """
        Get or create a firewall.
        """
        if not tutorial.expose_ports:
            logger.info("No ports for expose, no firewall needed.")
            return

        self.ensure_ingress_firewall(tutorial)
        self.ensure_egress_firewall(tutorial)

    def ensure_ingress_firewall(self, tutorial):
        raise NotImplementedError

    def ensure_egress_firewall(self, tutorial):
        raise NotImplementedError

    def instances(self, *args, **kwargs):
        raise NotImplementedError(
            "The instances function is not implemented for this class."
        )

    def stop(self, *args, **kwargs):
        raise NotImplementedError(
            "The stop function is not implemented for this class."
        )

    def deploy(self, *args, **kwargs):
        raise NotImplementedError(
            "The deploy function is not implemented for this class."
        )
