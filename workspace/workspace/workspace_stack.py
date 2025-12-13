from aws_cdk import (
    aws_ec2 as ec2,
    Stack,
)

from constructs import Construct

class WorkspaceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        source_ami = "ami-0f5fcdfbd140e4ab7"
        default_vpc = ec2.Vpc.from_lookup(self, 'DefaultVPC',
            is_default=False
        )

        publicKey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDCIZGs+NXLVki+CR9u200ehxdSE7XzljFzQXiKLObPZlWdo0MEKuxpCGhVuxqhJjPYhh2zG/AJggRzuLg/FZdxDT+cIITVii11Vxl2Ry/h3DHvJKMptZfOtzCeEoUvoTg2Mj8ets1EMc0WrmG9tSNKh5oCqmGfn2AnLrGUkXfabG9BgRJIPYciDLqVpC8eQ+QZmCQY7r78SIc8c78wsPBqn5j5yjaNbLXIyAAduZgwJ3FUO9j541+0qOQxREIvVgE4M/7sVoPA+emZPc+HOXw8D3U8BQGyn40GaGJM20N9odc2qVHquD1V6O9qjO0aj4L7GZtDBeowjw2tUyKoYbV7tatU/AiQX1DaNitdVoh3t1HQGfshz+Cy7Nh2uFIDeypvwrXfHMVmGeDTnPuCdzKUi3eAT0V4XsJpQLC3jR5CcbX5BVN6lACaxFmhy3nl2adxbKpHrNbdtXhDhCMG8B9xI0WHwKZviQ5LCLPbslz5WdTbKHwHu2p7S76W9taglPYEKMmf8rwvHj9u/5ysmFH0X4YThjvlyvWheLmlxrpQSL9VzrQ7FcBgLU/+beHgDFY6e/pYz22KzGyZrgbwseee1dC1VKwkcTkMuUFcAvUqaQSF9hucts5NwA/ZpGxwslzK5sVaWkZafzkDN7/iYuHS1N3vjUIkE/sA8xaWJvfL4Q== russest3@pop-os"

        keyPair = ec2.KeyPair(self, "KubernetesKeyPair",
            account="014420964653",
            key_pair_name="KubernetesKeyPair",
            region="us-east-2",
            public_key_material=publicKey,
        )

        control_plane_sg = ec2.SecurityGroup(
            self,
            "ControlPlaneSG",
            vpc=default_vpc,
            description="Control Plane Security Group",
            allow_all_outbound=True,
        )

        control_plane_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "allow ssh access from the world"
        )

        c1_cp1_user_data = ec2.UserData.for_linux()
        c1_cp1_user_data.add_commands(
            "#!/usr/bin/bash",
            "apt update -y",
            "apt upgrade -y",
            "add-apt-repository -y ppa:deadsnakes/ppa",
            "apt install -y python3.10 python3-pip python3-apt python3-venv containerd apt-transport-https ca-certificates curl gpg net-tools",
            "apt update -y",
            "apt upgrade -y",
            "sed -i 's/^#\s*PasswordAuthentication.*$/PasswordAuthentication yes/' /etc/ssh/sshd_config",
            "sed -i 's/^KbdInteractiveAuthentication.*$/#KbdInteractiveAuthentication no/' /etc/ssh/sshd_config",
            "systemctl restart ssh",
            "echo 'overlay' > /etc/modules-load.d/k8s.conf",
            "echo 'br_netfilter' >> /etc/modules-load.d/k8s.conf",
            "modprobe overlay",
            "modprobe br_netfilter",
            "echo 'net.bridge.bridge-nf-call-iptables=1' | tee -a /etc/sysctl.conf",
            "echo 'net.bridge.bridge-nf-call-ip6tables=1' | tee -a /etc/sysctl.conf",
            "sed -i 's/^#net.ipv4.ip_forward.*$/net.ipv4.ip_forward=1/' /etc/sysctl.conf",
            "sysctl -p",
            "mkdir /etc/containerd",
            "containerd config default | tee /etc/containerd/config.toml",
            "sed -i 's/            SystemdCgroup = false/            SystemdCgroup = true/' /etc/containerd/config.toml",
            "curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg",
            "echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list",
            "apt update -y",
            "apt install -y kubelet kubeadm kubectl",
            "apt-mark hold kubelet kubeadm kubectl containerd",
            "mkdir -p /home/ubuntu/.kube",
            "chown ubuntu:ubuntu /home/ubuntu/.kube",
            "wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml -o /home/ubuntu/kube-flannel.yml",
            "curl -O https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3",
            "bash ./get-helm-3",
            "reboot",
        )

        c1_cp1 = ec2.Instance(self, "ControlNode",
            vpc=default_vpc,
            instance_name="c1-cp1",
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC ),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.generic_linux({"us-east-2": source_ami}),
            security_group=control_plane_sg,
            key_pair=keyPair,
            user_data=c1_cp1_user_data,
            user_data_causes_replacement=True,
        )
