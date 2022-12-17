# Copyright 2022 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import time

from ..base import Backend


class GoogleCloud(Backend):
    """
    A Google Cloud backend
    """

    name = "google"

    def __init__(self, **kwargs):
        self.zone = kwargs.get("zone") or "us-central1-a"
        self.project = None
        self.compute_cli = None
        try:
            self._set_services()
        except Exception as e:
            raise ValueError(f"Cannot create Google Cloud backend {e}")
        super(GoogleCloud, self).__init__(settings=kwargs.get("settings"))

    def _set_services(self):
        """
        Use Google Discovery Build to generate an API client for compute and billing.
        """
        import google.auth
        import google_auth_httplib2
        import googleapiclient
        import httplib2
        from googleapiclient.discovery import build as discovery_build

        # Get default credentials. If there is an exception, caught by init function
        # google.auth.DefaultCredentialsError
        creds, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.project = project

        def build_request(_, *args, **kwargs):
            """
            See https://googleapis.github.io/google-api-python-client/docs/thread_safety.html

            Note that the first positional arg (http) is required despite not being used here.
            """
            new_http = google_auth_httplib2.AuthorizedHttp(creds, http=httplib2.Http())
            return googleapiclient.http.HttpRequest(new_http, *args, **kwargs)

        # Discovery client for Google Cloud Compute
        # https://cloud.google.com/compute/docs/reference/rest/v1/instances
        authorized_http = google_auth_httplib2.AuthorizedHttp(creds)
        self.compute_cli = discovery_build(
            "compute",
            "v1",
            cache_discovery=False,
            http=authorized_http,
            requestBuilder=build_request,
        )

    def deploy(self, tutorial, envars=None):
        """
        Deploy to Google Cloud
        """
        # TODO check for existing instance with same slug here
        # TODO use cloud-select here to get an instance that matches memory
        instance = self.settings["instance"]
        zone = self.settings.get("zone") or self.zone

        start_script = tutorial.prepare_startup_script(envars)
        body = {
            "machineType": f"projects/{self.project}/zones/{zone}/machineTypes/{instance}",
            "name": tutorial.slug,
            "canIpForward": True,
            "tags": {"items": ["http-server", "https-server"]},
            "disks": [
                {
                    "boot": True,
                    "autoDelete": True,
                    "initializeParams": {
                        "sourceImage": "projects/debian-cloud/global/images/family/debian-10"
                    },
                }
            ],
            "metadata": {"items": [{"key": "startup-script", "value": start_script}]},
            "networkInterfaces": [{"accessConfigs": [{"type": "ONE_TO_ONE_NAT"}]}],
        }

        # At this point the upper level client has already validated envars
        request = self.compute_cli.instances().insert(
            project=self.project, zone=zone, body=body
        )
        response = self._retry_request(request)
        print(response)
        # TODO need to get network interface working / connect command

    def _retry_request(self, request, timeout=2, attempts=3):
        """
        The Google Python API client frequently has BrokenPipe errors. This
        function takes a request, and executes it up to number of retry,
        each time with a 2* increase in timeout.
        """
        import googleapiclient

        try:
            return request.execute()
        except BrokenPipeError as e:
            if attempts > 0:
                time.sleep(timeout)
                return self._retry_request(
                    request, timeout=timeout * 2, attempts=attempts - 1
                )
            raise e
        except googleapiclient.errors.HttpError as e:
            if attempts > 0:
                time.sleep(timeout)
                return self._retry_request(
                    request, timeout=timeout * 2, attempts=attempts - 1
                )
            raise e
        except Exception as e:
            if attempts > 0:
                time.sleep(timeout)
                return self._retry_request(
                    request, timeout=timeout * 2, attempts=attempts - 1
                )
            raise e
