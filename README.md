# Build out a Kubernetes Cluster in an AWS VPC with Client VPN Endpoint using Cloud Development Kit in 5 minutes!

## Architecture

![]()

## Requirements

- AWS CDK installed
- AWS CLI installed
- Run `aws configure` to configure access keys

## AWS CDK Procedure
```
$ cd workspace
$ cdk deploy
```

After the infrastructure is built out run the Ansible Playbook to configure the cluster

```
ansible-playbook automated_install.yml -i inventory -v
```

# This requires a key!!! How to automate this or put in README?
SSH to an instance with

```
ssh ubuntu@c1-cp1 -i ~/.ssh/<key>.pub
```

Setup kubectl locally:

```
kubectl config set-cluster mycluster --server=https://<public_ip>:6443 --certificate-authority=ca.crt
kubectl config set-credentials ubuntu --client-certificate=~/.ssh/id_rsa.pub --client-key=~/.ssh/id_rsa
kubectl config set-context current --cluster=mycluster --user=ubuntu
```

Enjoy!