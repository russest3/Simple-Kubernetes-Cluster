from aws_cdk import (
    aws_iam as iam,
    aws_ec2 as ec2,
    Stack,
)
from constructs import Construct

class WorkspaceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ami_id = "ami-0529b091671d10bda"  # Updated to 1.34 ! 12/13

        publicKey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDCIZGs+NXLVki+CR9u200ehxdSE7XzljFzQXiKLObPZlWdo0MEKuxpCGhVuxqhJjPYhh2zG/AJggRzuLg/FZdxDT+cIITVii11Vxl2Ry/h3DHvJKMptZfOtzCeEoUvoTg2Mj8ets1EMc0WrmG9tSNKh5oCqmGfn2AnLrGUkXfabG9BgRJIPYciDLqVpC8eQ+QZmCQY7r78SIc8c78wsPBqn5j5yjaNbLXIyAAduZgwJ3FUO9j541+0qOQxREIvVgE4M/7sVoPA+emZPc+HOXw8D3U8BQGyn40GaGJM20N9odc2qVHquD1V6O9qjO0aj4L7GZtDBeowjw2tUyKoYbV7tatU/AiQX1DaNitdVoh3t1HQGfshz+Cy7Nh2uFIDeypvwrXfHMVmGeDTnPuCdzKUi3eAT0V4XsJpQLC3jR5CcbX5BVN6lACaxFmhy3nl2adxbKpHrNbdtXhDhCMG8B9xI0WHwKZviQ5LCLPbslz5WdTbKHwHu2p7S76W9taglPYEKMmf8rwvHj9u/5ysmFH0X4YThjvlyvWheLmlxrpQSL9VzrQ7FcBgLU/+beHgDFY6e/pYz22KzGyZrgbwseee1dC1VKwkcTkMuUFcAvUqaQSF9hucts5NwA/ZpGxwslzK5sVaWkZafzkDN7/iYuHS1N3vjUIkE/sA8xaWJvfL4Q== russest3@pop-os"

        keyPair = ec2.KeyPair(self, "KubernetesKeyPair",
            account="014420964653",
            key_pair_name="KubernetesKeyPair",
            region="us-east-2",
            public_key_material=publicKey,
        )

        vpc = ec2.Vpc(self, "Vpc",
            max_azs=1,
            cidr="10.192.0.0/16",
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24, 
                )
            ]
        )

        # keyPair = ec2.KeyPair.from_key_pair_attributes(self, "KeyPair",
        #             key_pair_name="KubernetesKeyPair",
        #             type=ec2.KeyPairType.RSA
        #         )
        
        ec2_role = iam.Role(self, "Ec2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            role_name="Ec2Role"
        )

        for i in ["AmazonSSMManagedInstanceCore", "CloudWatchLogsFullAccess"]:
            ec2_role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name(i)
            )

        control_plane_sg = ec2.SecurityGroup(
            self,
            "ControlPlaneSG",
            vpc=vpc,
            description="Control Plane Security Group",
            allow_all_outbound=True,
        )

        control_plane_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh access from the world"
        )

        control_plane_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(6443), "For Cluster API"
        )

        worker_node_sg = ec2.SecurityGroup(
            self,
            "WorkerNodeSG",
            vpc=vpc,
            description="Worker Node Security Group",
            allow_all_outbound=True,
        )

        worker_node_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh access from the world"
        )

        c1_cp1_user_data = ec2.UserData.for_linux()
        c1_cp1_user_data.add_commands(
            "hostnamectl hostname c1-cp1",
            "apt update -y",
            "apt upgrade -y",
            "kubeadm init --kubernetes-version v1.34.1 --pod-network-cidr=10.244.0.0/16 --upload-certs --ignore-preflight-errors=NumCPU,Mem",
            "cp /etc/kubernetes/admin.conf /home/ubuntu/.kube/config",
            "chown ubuntu:ubuntu /home/ubuntu/.kube/config",
            "kubeadm token create --print-join-command",
            "cp /root/kube-flannel.yml /home/ubuntu/",
            "chown ubuntu: /home/ubuntu/kube-flannel.yml"
            "sudo su - ubuntu"
            "kubectl apply -f /home/ubuntu/kube-flannel.yml",
        )

        c1_cp1 = ec2.Instance(self, "ControlNode",
            vpc=vpc,
            instance_name="c1-cp1",
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC ),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.SMALL),
            machine_image=ec2.MachineImage.generic_linux({"us-east-2": ami_id}),
            role=ec2_role,
            security_group=control_plane_sg,
            key_pair=keyPair,
            user_data=c1_cp1_user_data,
            user_data_causes_replacement=True,
        )

        c1_node1_user_data = ec2.UserData.for_linux()
        c1_node1_user_data.add_commands(
            "hostnamectl hostname c1-node1",
            "apt update -y",
            "apt upgrade -y",
        )

        c1_node1 = ec2.Instance(self, "WorkerNode1",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.generic_linux({"us-east-2": ami_id}),
            instance_name="c1-node1",
            security_group=worker_node_sg,
            role=ec2_role,
            user_data=c1_node1_user_data,
            user_data_causes_replacement=True,
            key_pair=keyPair,
        )

        # c1_node2_user_data = ec2.UserData.for_linux()
        # c1_node2_user_data.add_commands(
        #     "hostname c1-node2",
        #     "echo 'c1-node2 > /etc/hostname'",
        #     "apt update -y",
        #     "apt upgrade -y",
        # )

        # c1_node2 = ec2.Instance(self, "WorkerNode2",
        #     vpc=vpc,
        #     vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
        #     instance_name="c1-node2",
        #     instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
        #     machine_image=ec2.MachineImage.generic_linux({"us-east-2": ami_id}),
        #     security_group=worker_node_sg,
        #     role=ec2_role,
        #     user_data=c1_node2_user_data,
        #     user_data_causes_replacement=True,
        #     key_pair=keyPair,
        # )
