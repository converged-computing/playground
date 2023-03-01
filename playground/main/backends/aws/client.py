# Copyright 2022-2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import operator
import os
import time

from cloud_select.main.selectors import InstanceSelector

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
        vpc.create_tags(Tags=[{"Key": "Name", "Value": tutorial.uid}])
        return vpc

    def detach_gateways(self, vpc):
        """
        Detach gateways (and if there is an issue, try again)
        """
        logger.info("Detaching gateways...")
        for attach in self.ec2_client.describe_transit_gateway_attachments()[
            "TransitGatewayAttachments"
        ]:
            if attach["ResourceId"] == vpc.vpc_id:
                self.ec2_client.delete_transit_gateway_vpc_attachment(
                    TransitGatewayAttachmentId=attach["TransitGatewayAttachmentId"]
                )

        logger.info("Deleting Network Address Translation (NAT) Gateways...")
        filters = [{"Name": "vpc-id", "Values": [vpc.vpc_id]}]
        for gateway in self.ec2_client.describe_nat_gateways(Filters=filters)[
            "NatGateways"
        ]:
            self.ec2_client.delete_nat_gateway(NatGatewayId=gateway["NatGatewayId"])

        # Associate default options
        options = self.ec2_resources.DhcpOptions("default")
        if options:
            options.associate_with_vpc(VpcId=vpc.id)

    def _release_instance_addresses(self, vpc):
        """
        Release instance addresses before we delete them.
        """
        # Release addresses from instances
        for subnet in vpc.subnets.all():
            for instance in subnet.instances.all():
                filters = [{"Name": "instance-id", "Values": [instance.id]}]
                addresses = self.ec2_client.describe_addresses(Filters=filters)[
                    "Addresses"
                ]
                for address in addresses:
                    self.ec2_client.disassociate_address(
                        AssociationId=address["AssociationId"]
                    )
                    self.ec2_client.release_address(
                        AllocationId=address["AllocationId"]
                    )

    def delete_peers(self, vpc):
        """
        Delete peers connections
        """
        logger.info("Deleting peer connections...")
        for peer in self.ec2_client.describe_vpc_peering_connections()[
            "VpcPeeringConnections"
        ]:
            if peer["AccepterVpcInfo"]["VpcId"] == vpc.vpc_id:
                conn = self.ec2_resources.VpcPeeringConnection(
                    peer["VpcPeeringConnectionId"]
                )
                self.delete_with_backoff(conn)
            if peer["RequesterVpcInfo"]["VpcId"] == vpc.vpc_id:
                conn = self.ec2_resources.VpcPeeringConnection(
                    peer["VpcPeeringConnectionId"]
                )
                self.delete_with_backoff(conn)

    def _wait_for_network_interfaces_deletion(self, vpc):
        """
        Wait for all network interfaces to be deleted before continuing!
        """
        filters = [{"Name": "vpc-id", "Values": [vpc.vpc_id]}]
        logger.info("Waiting for network interface deletion...")
        sleep = 2
        deleted = False

        while not deleted:
            if not self.ec2_client.describe_network_interfaces(Filters=filters)[
                "NetworkInterfaces"
            ]:
                deleted = True
                break
            else:
                time.sleep(sleep)
                sleep = sleep * 2

    def delete_subnets(self, vpc):
        """
        Delete subnets
        """
        for subnet in vpc.subnets.all():
            for interface in subnet.network_interfaces.all():
                self.delete_with_backoff(interface)
            self.delete_with_backoff(subnet)

    def delete_vpc(self, tutorial):
        """
        Delete the vpc and subnets, etc.
        """
        vpc = self.get_vpc(tutorial)
        if not vpc:
            logger.info("There is no VPC to delete.")
            return

        self.delete_instances(vpc)

        # Detach internet gateways, delete peers
        self.detach_gateways(vpc)
        self.delete_peers(vpc)

        # Finally delete VPC endpoints
        for endpoint in self.ec2_client.describe_vpc_endpoints(
            Filters=[{"Name": "vpc-id", "Values": [vpc.vpc_id]}]
        )["VpcEndpoints"]:
            self.ec2_client.delete_vpc_endpoints(
                VpcEndpointIds=[endpoint["VpcEndpointId"]]
            )

        self.delete_security_groups(vpc)

        # delete custom Network ACLs
        for netacl in vpc.network_acls.all():
            if not netacl.is_default:
                netacl.delete()

        # Wait for network interfaces to be deleted
        self._wait_for_network_interfaces_deletion(vpc)
        self.delete_subnets(vpc)
        self.delete_routing_tables(tutorial)
        self.delete_gateways(vpc)

        # Delete vpc (this can take some time)
        logger.info("Deleting VPC...")
        self.ec2_client.delete_vpc(VpcId=vpc.vpc_id)

    def delete_gateways(self, vpc):
        """
        After detach, delete the gateways.
        """
        filters = [{"Name": "vpc-id", "Values": [vpc.vpc_id]}]
        ids = [
            g["NatGatewayId"]
            for g in self.ec2_client.describe_nat_gateways(Filters=filters)[
                "NatGateways"
            ]
        ]
        for gateway_id in ids:
            self.ec2_client.delete_nat_gateway(NatGatewayId=gateway_id)

        for gateway in vpc.internet_gateways.all():
            vpc.detach_internet_gateway(InternetGatewayId=gateway.id)
            self.delete_with_backoff(gateway)

    def delete_with_backoff(self, obj):
        """
        Shared function to delete with simple backoff.
        """
        deleted = False
        sleep = 2
        while not deleted:
            try:
                obj.delete()
                deleted = True
            except Exception as e:
                logger.warning(
                    f"Not able to delete yet: {e} Trying again in {sleep} seconds."
                )
                time.sleep(sleep)
                sleep = sleep * 2

    def get_vpc(self, tutorial):
        """
        Get a VPC with tags for the playground-tutorial
        """
        response = self.ec2_client.describe_vpcs(
            Filters=[{"Name": "tag:Name", "Values": [tutorial.uid]}]
        )
        if response["Vpcs"]:
            return self.ec2_resources.Vpc(response["Vpcs"][0]["VpcId"])

    def ensure_gateway(self, tutorial, vpc):
        """
        Ensure we have an internet gateway.
        """
        response = self.ec2_client.describe_internet_gateways(
            Filters=[{"Name": "tag:playground-tutorial", "Values": [tutorial.uid]}]
        )
        if response["InternetGateways"]:
            for subnet in vpc.subnets.iterator():
                return subnet

        # Create the Internet Gateway and attach to our VPC
        ig = self.ec2_client.create_internet_gateway(
            TagSpecifications=self.get_tags("internet-gateway", tutorial)
        )
        ig_uid = ig["InternetGateway"]["InternetGatewayId"]
        vpc.attach_internet_gateway(InternetGatewayId=ig_uid)

        # Create routing table
        rt = vpc.create_route_table()
        rt.create_route(DestinationCidrBlock="0.0.0.0/0", GatewayId=ig_uid)
        rt.create_tags(Tags=[{"Key": "Name", "Value": tutorial.uid}])

        # And public subnet, associated with routine table
        subnet = vpc.create_subnet(
            CidrBlock=self.cidr_block,
            AvailabilityZone="{}{}".format(self.regions[0], self.zone),
        )
        subnet.create_tags(Tags=[{"Key": "Name", "Value": tutorial.uid}])
        rt.associate_with_subnet(SubnetId=subnet.id)
        return subnet

    def ensure_security_group(self, tutorial, vpc):
        """
        Ensure we create the security group.
        """
        try:
            return self.ec2_client.describe_security_groups(
                Filters=[{"Name": "group-name", "Values": [tutorial.uid]}]
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
            GroupName=tutorial.uid,
            Description=f"Security group for {tutorial.uid}",
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
        key_file = "{}.pem".format(tutorial.uid)
        if os.path.exists(key_file):
            return tutorial.uid

        # Does the keypair exist?
        key_pairs = self.ec2_client.describe_key_pairs(KeyNames=[tutorial.uid]).get(
            "KeyPairs"
        )
        if key_pairs:
            logger.debug(
                f"Key pair for {tutorial.uid} already exists, deleting to re-create."
            )
            key_pair = key_pairs[0]
            self.ec2_client.delete_key_pair(KeyName=tutorial.uid)

        # Always create a new one
        key_pair = self.ec2_client.create_key_pair(KeyName=tutorial.uid)
        with open(key_file, "w") as pk:
            pk.write(dict(key_pair)["KeyMaterial"])
        return tutorial.uid

    def delete_pem(self, tutorial):
        """
        Delete key pair file.
        """
        # If we already have the key file, return the identifier
        key_file = "{}.pem".format(tutorial.uid)
        if os.path.exists(key_file):
            logger.info("Deleting pem...")
            os.remove(key_file)

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
        instances = self.get_instances(tutorial.uid)
        if not instances:
            logger.info("There are no instances to stop.")
            return

        # shutdown should terminate
        ids = [
            x["InstanceId"]
            for x in instances
            if x["State"]["Name"] not in ["stopped", "terminated"]
        ]
        if ids:
            logger.info("Stopping instance...")
            self.ec2_client.stop_instances(InstanceIds=ids)

    def delete_instances(self, vpc):
        """
        Terminate all instances associated with a VPC
        """
        self._release_instance_addresses(vpc)

        filters = [{"Name": "vpc-id", "Values": [vpc.vpc_id]}]
        instances = self.ec2_client.describe_instances(Filters=filters)
        ids = []

        # Ensure we delete reservations
        for res in instances["Reservations"]:
            ids += [instance["InstanceId"] for instance in res["Instances"]]

        if ids:
            logger.info("Waiting for instances to terminate")
            waiter = self.ec2_client.get_waiter("instance_terminated")
            self.ec2_client.terminate_instances(InstanceIds=ids)
            try:
                waiter.wait(InstanceIds=ids)
            except Exception as e:
                logger.warning(e)

    def stop_gateways(self, tutorial):
        """
        Stop and delete internet gateways.
        """
        gateways = self.get_gateways(tutorial.uid)
        if not gateways:
            logger.info("There are no gateways to stop.")
            return
        for gateway in gateways:
            self.ec2_client.delete_internet_gateway(
                InternetGatewayId=gateway["InternetGatewayId"]
            )

    def delete_security_groups(self, vpc):
        """
        Clean up the security groups
        """
        # We use the id because using group name assumes default VPC
        logger.info("Deleting security groups...")
        for sg in vpc.security_groups.all():
            for ingress in sg.ip_permissions:
                kwargs = {
                    "DryRun": False,
                    "GroupId": sg.group_id,
                    "IpPermissions": [ingress],
                }
                self.ec2_client.revoke_security_group_ingress(**kwargs)

            for egress in sg.ip_permissions_egress:
                kwargs = {
                    "DryRun": False,
                    "GroupId": sg.group_id,
                    "IpPermissions": [egress],
                }
                self.ec2_client.revoke_security_group_egress(**kwargs)

            if sg.group_name != "default":
                self.delete_with_backoff(sg)

    def delete_routing_tables(self, tutorial):
        """
        Clean up routing tables
        """
        tables = self.get_routing_tables(tutorial.uid)
        if not tables:
            logger.info("There are no routing tables to delete.")
            return
        for table in tables:
            for route in table["Routes"]:
                if route["Origin"] == "CreateRoute":
                    self.ec2_client.delete_route(
                        RouteTableId=table["RouteTableId"],
                        DestinationCidrBlock=route["DestinationCidrBlock"],
                    )

            for assoc in table["Associations"]:
                if not assoc["Main"]:
                    self.ec2_client.disassociate_route_table(
                        AssociationId=assoc["RouteTableAssociationId"]
                    )
                    self.ec2_client.delete_route_table(
                        RouteTableId=table["RouteTableId"]
                    )

        tables = self.get_routing_tables(tutorial.uid)
        for table in tables:
            if table["Associations"] == []:
                self.ec2_client.delete_route_table(RouteTableId=table["RouteTableId"])

    def get_routing_tables(self, name):
        """
        Get routing tables that match the playground-tutorial tags.
        """
        tables = []
        for table in self.ec2_client.describe_route_tables(
            Filters=[{"Name": "tag:Name", "Values": [name]}]
        ).get("RouteTables", []):
            for tag in table.get("Tags", []):
                if tag["Key"] == "Name" and tag["Value"] == name:
                    tables.append(table)
        return tables

    def stop(self, tutorial):
        """
        Stop a tutorial
        """
        # This is a huge dependency hairball that is hard to get right
        self.delete_vpc(tutorial)

        # This is not :)
        self.delete_pem(tutorial)

    def get_tags(self, resource, tutorial):
        """
        Get tags for any tutorial resource.
        """
        # We will use tags to identify it later
        return [
            {
                "ResourceType": resource,
                "Tags": [
                    {"Key": "playground-tutorial", "Value": tutorial.uid},
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
                    if (
                        tag["Key"] == "playground-tutorial"
                        and tag["Value"] == name
                        and instance["State"]["Name"] != "terminated"
                    ):
                        return True
        return False

    def select_instance(self, tutorial):
        """
        Run cloud select to choose tutorial instance based on lowest price.
        """
        selector = InstanceSelector(cloud="aws", regions=self.regions)

        # We don't set a default so we can detect None and tell the user we are choosing default
        instance = selector.select_instance(tutorial.flexible_resources)
        if not instance:
            instance = self.settings["instance"]
            logger.info(f"Using default instance {instance}")
        return instance

    def deploy(self, tutorial, envars=None, **kwargs):
        """
        Deploy to AWS

        This article was hugely helpful to get the ordering and relationship of things
        correct! https://arjunmohnot.medium.com/aws-ec2-management-with-python-and-boto-3-59d849f1f58f
        """
        # If we have matching regions, use cloud select, otherwise default
        instance = self.select_instance(tutorial)
        logger.info(f"You have selected {instance}")

        # Figure out if it's already running
        if self.instance_exists(tutorial.uid):
            logger.info(f"Instance {tutorial.uid} is already running.")
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
        res.create_tags(Tags=[{"Key": "Name", "Value": tutorial.uid}])
        res.wait_until_running()
        url = res.public_ip_address

        # Show the ip address, and give a warning about startup time
        self.show_ip_address(url, tutorial)
