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

Enjoy!