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

Install nginx gateway fabric

```
kubectl kustomize "https://github.com/nginx/nginx-gateway-fabric/config/crd/gateway-api/standard?ref=v2.2.2" | kubectl apply -f -

helm install ngf oci://ghcr.io/nginx/charts/nginx-gateway-fabric --create-namespace -n nginx-gateway --set nginx.service.type=NodePort --set-json 'nginx.service.nodePorts=[{"port":31437,"listenerPort":80}]'

gateway-class.yaml:

apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: nginx
  namespace: nginx-gateway
spec:
  controllerName: nginx.org/nginx-gateway-controller

http gateway and listener:

apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: nginx-gateway
  namespace: nginx-gateway
spec:
  gatewayClassName: nginx
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All

```

Enjoy!