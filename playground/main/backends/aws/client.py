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
        vpc = self.get_vpc(tutorial)
        if vpc:
            return vpc

        new_vpc = self.ec2_client.create_vpc(
            CidrBlock=self.cidr_block, TagSpecifications=self.get_tags("vpc", tutorial)
        )
        vpc = self.ec2_resources.Vpc(new_vpc["Vpc"]["VpcId"])
        vpc.create_tags(Tags=[{"Key": "Name", "Value": tutorial.slug}])
        return vpc

    def delete_vpc(self, tutorial):
        """
        Delete the vpc and subnets, etc.
        """
        vpc = self.get_vpc(tutorial)
        if not vpc:
            logger.info("There is no VPC to delete.")
            return

        # Delete subnets
        for subnet in vpc.subnets.iterator():
            subnet.delete()

        # Detach internet gateways
        for gateway in vpc.internet_gateways.iterator():
            vpc.detach_internet_gateway(InternetGatewayId=gateway.id)
            gateway.delete()

        # Delete routing tables and vpc (this seems to handle both)
        vpc.delete()

    def get_vpc(self, tutorial):
        """
        Get a VPC with tags for the playground-tutorial
        """
        response = self.ec2_client.describe_vpcs(
            Filters=[{"Name": "tag:Name", "Values": [tutorial.slug]}]
        )
        if response["Vpcs"]:
            return self.ec2_resources.Vpc(response["Vpcs"][0]["VpcId"])

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

    def stop_instance(self, tutorial):
        """
        Stop an instance.
        """
        instances = self.get_instances(tutorial.slug)
        if not instances:
            logger.info("There are no instances to stop.")
            return

        # shutdown should terminate
        ids = [x["InstanceId"] for x in instances]
        self.ec2_client.stop_instances(InstanceIds=ids)

    def stop_gateways(self, tutorial):
        """
        Stop and delete internet gateways.
        """
        gateways = self.get_gateways(tutorial.slug)
        if not gateways:
            logger.info("There are no gateways to stop.")
            return
        for gateway in gateways:
            self.ec2_client.delete_internet_gateway(
                InternetGatewayId=gateway["InternetGatewayId"]
            )

    def delete_security_group(self, tutorial):
        """
        Clean up the security groups
        """
        sgs = self.get_security_groups(tutorial.slug)
        if not sgs:
            logger.info("There are no security groups to delete.")
            return

        # We use the id because using group name assumes default VPC
        for sg in sgs:
            self.ec2_client.delete_security_group(GroupId=sg["GroupId"])

    def delete_routing_tables(self, tutorial):
        """
        Clean up routing tables
        """
        tables = self.get_routing_tables(tutorial.slug)
        if not tables:
            logger.info("There are no routing tables to delete.")
            return
        for table in tables:
            self.ec2_client.delete_route_table(RouteTableId=table["RouteTableId"])

    def get_routing_tables(self, name):
        """
        Get routing tables that match the playground-tutorial tags.
        """
        tables = []
        for table in self.ec2_client.describe_route_tables(
            Filters=[{"Name": "tag:Name", "Values": [name]}]
        ).get("RouteTables", []):
            print(table)
            for tag in table.get("Tags", []):
                if tag["Key"] == "Name" and tag["Value"] == name:
                    tables.append(table)
        return tables

    def stop(self, tutorial):
        """
        Stop a tutorial
        """
        # Figure out if it's already running
        if self.instance_exists(tutorial.slug):
            self.stop_instance(tutorial)

        # Clean up security groups
        self.delete_security_group(tutorial)

        # This deletes routing table, vpc, and subnet
        self.delete_vpc(tutorial)

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

    def get_gateways(self, name):
        """
        Get all internet gateways with a playground-tutorial tag.
        """
        gateways = []
        for group in self.ec2_client.describe_internet_gateways().get(
            "InternetGateways", []
        ):
            for tag in group.get("Tags", []):
                if tag["Key"] == "playground-tutorial" and tag["Value"] == name:
                    gateways.append(group)
        return gateways

    def get_security_groups(self, name):
        """
        Get all security groups with a playground-tutorial tag.
        """
        sgs = []
        for group in self.ec2_client.describe_security_groups().get(
            "SecurityGroups", []
        ):
            if group["GroupName"] == name:
                sgs.append(group)
        return sgs

    def get_instances(self, name):
        """
        Get all instances with a playground-tutorial tag.
        """
        instances = []
        for group in self.list_instances().get("Reservations", {}):
            for instance in group.get("Instances", []):
                for tag in instance.get("Tags", []):
                    if tag["Key"] == "playground-tutorial" and tag["Value"] == name:
                        instances.append(instance)
        return instances

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

        This article was hugely helpful to get the ordering and relationship of things
        correct! https://arjunmohnot.medium.com/aws-ec2-management-with-python-and-boto-3-59d849f1f58f
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

        params = {
            "ImageId": ami,
            "InstanceType": instance,
            "UserData": start_script,
            "TagSpecifications": self.get_tags("instance", tutorial),
            "KeyName": pem,
            "NetworkInterfaces": networks,
            "InstanceInitiatedShutdownBehavior": "terminate",
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
