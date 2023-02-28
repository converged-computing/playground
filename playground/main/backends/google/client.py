# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import time

from cloud_select.main.selectors import InstanceSelector

import playground.logger as log
from playground.logger import logger

from ..base import Backend


class GoogleCloud(Backend):
    """
    A Google Cloud backend
    """

    name = "google"

    def __init__(self, **kwargs):
        self.zone = kwargs.get("zone") or "us-central1-a"
        self.regions = kwargs.get("regions") or ["us-central1"]
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

    def list_instances(self):
        """
        List running GCP instances.
        """
        request = self.compute_cli.instances().list(
            project=self.project, zone=self.zone
        )
        return self._retry_request(request)

    def firewall_exists(self, name):
        """
        Determine if a firewall exists.
        """
        # Here we are checking if it already exists
        request = self.compute_cli.firewalls().get(project=self.project, firewall=name)
        try:
            # We return if this is successful, it means it exists
            request.execute()
            return True
        except Exception:
            return False

    def ensure_ingress_firewall(self, tutorial):
        """
        Ensure the ingress firewall exists.
        """
        if self.firewall_exists(tutorial.firewall_ingress_name):
            return

        # If we have more than ports 80/443, create an INGRESS rule too
        create_ingress = False
        for port in tutorial.expose_ports:
            if port not in ["80", "443"]:
                create_ingress = True
                break

        if create_ingress:
            body = {
                "direction": "INGRESS",
                "description": f"Firewall ingress for tutorial {tutorial.name}.",
                "allowed": [
                    {
                        "IPProtocol": "tcp",
                        "ports": tutorial.expose_ports,
                    }
                ],
                "sourceRanges": ["0.0.0.0/0"],
                "targetTags": [tutorial.slug],
                "name": tutorial.firewall_ingress_name,
            }
            request = self.compute_cli.firewalls().insert(
                project=self.project, body=body
            )
            return self._retry_request(request)

    def ensure_egress_firewall(self, tutorial):
        """
        Ensure the egress firewall exists.
        """
        if self.firewall_exists(tutorial.firewall_egress_name):
            return

        # If we get down here we need to create the firewall, it doesn't exist yet
        body = {
            "direction": "EGRESS",
            "description": f"Firewall egress for tutorial {tutorial.name}.",
            "allowed": [
                {
                    "IPProtocol": "tcp",
                    "ports": tutorial.expose_ports,
                }
            ],
            "sourceRanges": ["0.0.0.0/0"],
            "targetTags": [tutorial.slug],
            "name": tutorial.firewall_egress_name,
        }
        request = self.compute_cli.firewalls().insert(project=self.project, body=body)
        return self._retry_request(request)

    def stop(self, tutorial):
        """
        Stop a tutorial
        """
        # Figure out if it's already running
        if not self.instance_exists(tutorial.slug):
            logger.info(f"Instance {tutorial.slug} is not running.")
            return
        zone = self.settings.get("zone") or self.zone

        # Delete the instance...
        request = self.compute_cli.instances().delete(
            project=self.project, zone=zone, instance=tutorial.slug
        )
        self._retry_request(request)

        def wait_until_stopped(cli, zone, tutorial):
            """
            Keep trying until we are completely stopped, and yield updates.
            """
            stopped = False
            while not stopped:
                request = cli.compute_cli.instances().get(
                    project=cli.project, zone=zone, instance=tutorial.slug
                )
                try:
                    response = cli._retry_request(request)
                except Exception:
                    stopped = True
                    break
                yield response["status"]
                if response["status"] == "TERMINATED":
                    stopped = True
                    break

        log.wrapped_wait(
            wait_until_stopped,
            kwargs={"cli": self, "tutorial": tutorial, "zone": zone},
            start_text="Waiting for instance to terminate...",
        )

        # and the firewalls TODO for multi-user mode we need an option to disable this,
        # or to make the firewalls (and instances) user-specific
        # TODO await for operation https://cloud.google.com/compute/docs/samples/compute-firewall-delete
        if self.firewall_exists(tutorial.firewall_egress_name):
            self._retry_request(
                self.compute_cli.firewalls().delete(
                    project=self.project, firewall=tutorial.firewall_egress_name
                )
            )

        if self.firewall_exists(tutorial.firewall_ingress_name):
            self._retry_request(
                self.compute_cli.firewalls().delete(
                    project=self.project, firewall=tutorial.firewall_ingress_name
                )
            )

    def instance_exists(self, name):
        """
        Determine if a tutorial instance exists.
        """
        existing = self.list_instances()
        for instance in existing.get("items", []):
            if instance["name"] == name:
                return True
        return False

    def select_instance(self, tutorial):
        """
        Run cloud select to choose tutorial instance based on lowest price.
        """
        selector = InstanceSelector(cloud="google", regions=self.regions)

        # We don't set a default so we can detect None and tell the user we are choosing default
        instance = selector.select_instance(tutorial.flexible_resources)
        if not instance:
            instance = self.settings["instance"]
            logger.info(f"Using default instance {instance}")
        return instance

    def deploy(self, tutorial, envars=None, **kwargs):
        """
        Deploy to Google Cloud

        See logs after ssh to instance:
        sudo journalctl -u google-startup-scripts.service
        """
        instance = self.select_instance(tutorial)
        zone = self.settings.get("zone") or self.zone
        logger.info(f"Selected instance {instance}")

        # Figure out if it's already running
        if self.instance_exists(tutorial.slug):
            logger.info(f"Instance {tutorial.slug} is already running.")
            return

        # Get the firewall (this returns a tag for the instance)
        self.ensure_firewall(tutorial)

        start_script = tutorial.prepare_startup_script(envars)
        body = {
            "machineType": f"projects/{self.project}/zones/{zone}/machineTypes/{instance}",
            "name": tutorial.slug,
            "canIpForward": True,
            # We add the firewall name here so it appears as a network tag
            "tags": {"items": ["http-server", "https-server", tutorial.slug]},
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

        # Get instance metadata
        request = self.compute_cli.instances().get(
            project=self.project, zone=zone, instance=tutorial.slug
        )
        url = None
        while not url:
            time.sleep(10)
            response = self._retry_request(request)
            if "natIP" not in response["networkInterfaces"][0]["accessConfigs"][0]:
                continue
            url = response["networkInterfaces"][0]["accessConfigs"][0]["natIP"]

        # If we have two default ports, assume there
        self.show_ip_address(url, tutorial)

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
