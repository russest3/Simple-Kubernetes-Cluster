from aws_cdk import (
    aws_iam as iam,
    aws_ec2 as ec2,
    Stack,
)
from constructs import Construct

class WorkspaceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ami_id = "ami-06d15e7bd1016764d"  # Updated to 1.34 ! 11/10

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

        keyPair = ec2.KeyPair.from_key_pair_attributes(self, "KeyPair",
                    key_pair_name="KubernetesKeyPair",
                    type=ec2.KeyPairType.RSA
                )
        
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

        worker_node_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(31984), "allow access to nodeports"
        )

        c1_cp1_user_data = ec2.UserData.for_linux()
        c1_cp1_user_data.add_commands(
            "hostname c1-cp1",
            "echo 'c1-cp1 > /etc/hostname'",
            "apt update -y",
            "apt upgrade -y",
            "kubeadm init --kubernetes-version v1.34.1 --pod-network-cidr=10.244.0.0/16 --upload-certs --ignore-preflight-errors=NumCPU,Mem",
            "mkdir -p /home/ubuntu/.kube",
            "chown ubuntu:ubuntu /home/ubuntu/.kube",
            "cp /etc/kubernetes/admin.conf /home/ubuntu/.kube/config",
            "chown ubuntu:ubuntu /home/ubuntu/.kube/config",
            "sudo su - ubuntu",
            "cd /home/ubuntu",
            "wget https://raw.githubusercontent.com/russest3/aws-vpc-with-client-vpn-endpoint/refs/heads/main/workspace/workspace/kube-flannel.yml",
            "kubectl apply -f /home/ubuntu/kube-flannel.yml",
            "wget https://get.helm.sh/helm-v4.0.0-rc.1-linux-amd64.tar.gz",
            "tar -xvzf helm*",
            "mv linux-amd64/helm /usr/bin/helm"
            "kubeadm token create --print-join-command",
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
            "hostname c1-node1",
            "echo 'c1-node1 > /etc/hostname'",
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

        c1_node2_user_data = ec2.UserData.for_linux()
        c1_node2_user_data.add_commands(
            "hostname c1-node2",
            "echo 'c1-node2 > /etc/hostname'",
            "apt update -y",
            "apt upgrade -y",
        )

        c1_node2 = ec2.Instance(self, "WorkerNode2",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_name="c1-node2",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.generic_linux({"us-east-2": ami_id}),
            security_group=worker_node_sg,
            role=ec2_role,
            user_data=c1_node2_user_data,
            user_data_causes_replacement=True,
            key_pair=keyPair,
        )
