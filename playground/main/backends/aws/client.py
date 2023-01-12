# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import operator
import os
import sys

from playground.logger import logger

from ..base import Backend


class AmazonCloud(Backend):
    """
    An AWS backend
    """

    name = "aws"

    def __init__(self, **kwargs):

        self.regions = kwargs.get("regions") or ["us-east-1"]
        self.zone = kwargs.get("zone") or "a"
        self.project = None
        self.ec2_client = None
        self.cidr_block = "192.168.1.0/24"

        # This currently has two pieces - billing and instances (different APIs)
        self._set_services()
        super(AmazonCloud, self).__init__()

    def _set_services(self):
        """
        Connect to needed amazon clients.

        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instance_types
        """
        import boto3

        self.ec2_client = boto3.client("ec2", region_name=self.regions[0])
        self.ec2_resources = boto3.resource("ec2", region_name=self.regions[0])

        try:
            self.ec2_client.describe_instances()
            self.has_instance_auth = True
        except Exception as e:
            logger.debug(f"Unable to authenticate to Amazon Web Services EC2: {e}")
            self.has_instance_auth = False

    def list_instances(self):
        """
        List running instances.
        """
        return self.ec2_client.describe_instances()

    def ensure_vpc(self, tutorial):
        """
        Ensure we have a VPC.

        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.create_vpc
        """
        response = self.ec2_client.describe_vpcs(
            Filters=[{"Name": "tag:Name", "Values": [tutorial.slug]}]
        )
        if response["Vpcs"]:
            return self.ec2_resources.Vpc(response["Vpcs"][0]["VpcId"])

        new_vpc = self.ec2_client.create_vpc(
            CidrBlock=self.cidr_block, TagSpecifications=self.get_tags("vpc", tutorial)
        )
        vpc = self.ec2_resources.Vpc(new_vpc["Vpc"]["VpcId"])
        vpc.create_tags(Tags=[{"Key": "Name", "Value": tutorial.slug}])
        return vpc

    def ensure_gateway(self, tutorial, vpc):
        """
        Ensure we have an internet gateway.
        """
        response = self.ec2_client.describe_internet_gateways(
            Filters=[{"Name": "tag:playground-tutorial", "Values": [tutorial.slug]}]
        )
        if response["InternetGateways"]:
            print("TODO ensure subsnet")
            import IPython

            IPython.embed()
            sys.exit()

        # Create the Internet Gateway and attach to our VPC
        ig = self.ec2_client.create_internet_gateway(
            TagSpecifications=self.get_tags("internet-gateway", tutorial)
        )
        ig_uid = ig["InternetGateway"]["InternetGatewayId"]
        vpc.attach_internet_gateway(InternetGatewayId=ig_uid)

        # Create routing table
        rt = vpc.create_route_table()
        rt.create_route(DestinationCidrBlock="0.0.0.0/0", GatewayId=ig_uid)
        rt.create_tags(Tags=[{"Key": "Name", "Value": tutorial.slug}])

        # And public subnet, associated with routine table
        subnet = vpc.create_subnet(
            CidrBlock=self.cidr_block,
            AvailabilityZone="{}{}".format(self.regions[0], self.zone),
        )
        subnet.create_tags(Tags=[{"Key": "Name", "Value": tutorial.slug}])
        rt.associate_with_subnet(SubnetId=subnet.id)

    def ensure_security_group(self, tutorial, vpc):
        """
        Ensure we create the security group.
        """
        try:
            return self.ec2_client.describe_security_groups(
                Filters=[{"Name": "group-name", "Values": [tutorial.slug]}]
            )["SecurityGroups"][0]
        except Exception:
            pass

        # Prepare permissions needed
        permissions = []
        for port in tutorial.expose_ports:
            permissions.append(
                {
                    "IpProtocol": "tcp",
                    "FromPort": int(port),
                    "ToPort": int(port),
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                }
            )

        # This can raise an error returned to top level client
        sg = self.ec2_client.create_security_group(
            GroupName=tutorial.slug,
            Description=f"Security group for {tutorial.slug}",
            VpcId=vpc.id,
        )

        logger.debug(f"Security Group {sg['GroupId']} in vpc {vpc.id}.")

        # Create ingress
        self.ec2_client.authorize_security_group_ingress(
            GroupId=sg["GroupId"], IpPermissions=permissions
        )
        return sg

    def ensure_pem(self, tutorial):
        """
        Ensure a key pair exists so we can connect to the instance.
        """
        # If we already have the key file, return the identifier
        key_file = "{}.pem".format(tutorial.slug)
        if os.path.exists(key_file):
            return tutorial.slug

        key_pair = self.ec2_client.create_key_pair(KeyName=tutorial.slug)
        with open(key_file, "w") as pk:
            pk.write(dict(key_pair)["KeyMaterial"])
        return tutorial.slug

    def get_ami(self):
        """
        Get the latest amazon Linux AMI
        """
        response = self.ec2_client.describe_images(
            Filters=[
                {
                    "Name": "description",
                    "Values": [
                        "Amazon Linux AMI*",
                    ],
                },
            ],
            Owners=["amazon"],
        )
        # Sort based on the creation date
        details = sorted(
            response["Images"], key=operator.itemgetter("CreationDate"), reverse=True
        )
        return details[0]["ImageId"]

    def stop(self, tutorial):
        """
        Stop a tutorial
        """
        # Figure out if it's already running
        if not self.instance_exists(tutorial.slug):
            logger.info(f"Instance {tutorial.slug} is not running.")
            return

        # zone = self.settings.get("zone") or self.zone

        # Delete security group
        try:
            self.ec2_client.delete_security_group(
                Filters=[{"Name": "group-name", "Values": [tutorial.slug]}]
            )
        except Exception:
            pass

    def get_tags(self, resource, tutorial):
        """
        Get tags for any tutorial resource.
        """
        # We will use tags to identify it later
        return [
            {
                "ResourceType": resource,
                "Tags": [
                    {"Key": "playground-tutorial", "Value": tutorial.slug},
                ],
            }
        ]

    def instance_exists(self, name):
        """
        Determine if a tutorial instance exists.
        """
        for group in self.list_instances().get("Reservations", {}):
            for instance in group.get("Instances", []):
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "playground-tutorial" and tag["Value"] == name:
                        return True
        return False

    def deploy(self, tutorial, envars=None):
        """
        Deploy to AWS
        """
        # TODO cloud select should choose based on memory here
        instance = self.settings["instance"]

        # Figure out if it's already running
        if self.instance_exists(tutorial.slug):
            logger.info(f"Instance {tutorial.slug} is already running.")
            return

        # Step 1: ensure we have VPC
        vpc = self.ensure_vpc(tutorial)

        # Step 2: We also need an internet gateway
        subnet = self.ensure_gateway(tutorial, vpc)
        sg = self.ensure_security_group(tutorial, vpc)

        # Step 3: and a pem file
        pem = self.ensure_pem(tutorial)

        ami = self.get_ami()
        start_script = tutorial.prepare_startup_script(envars)

        networks = [
            {
                "SubnetId": subnet.id,
                "DeviceIndex": 0,
                "AssociatePublicIpAddress": True,
                "Groups": [sg["GroupId"]],
            }
        ]

        # TODO we possibly should have key pair: https://www.learnaws.org/2020/12/16/aws-ec2-boto3-ultimate-guide/#how-to-create-an-ec2-key-pair
        params = {
            "ImageId": ami,
            "InstanceType": instance,
            "UserData": start_script,
            "TagSpecifications": self.get_tags("instance", tutorial),
            "KeyName": pem,
            "NetworkInterfaces": networks,
        }

        # Create the instance
        res = self.ec2_resources.create_instances(**params, MinCount=1, MaxCount=1)[0]
        res.create_tags(Tags=[{"Key": "Name", "Value": tutorial.slug}])
        res.wait_until_running()
        url = res.public_ip_address

        # If we have two default ports, assume there
        # TODO: add an https option to tutorial, and a config value for
        # which port we want the user to open!
        if len(tutorial.expose_ports) == 2:
            print(f"https://{url}")

        # Otherwise would be the last one
        else:
            print(f"https://{url}:{tutorial.expose_ports[-1]}")
