# ingress-nginx

Ingress controller for ONC Platform.

## Purpose

Routes HTTP/HTTPS traffic into the Kubernetes cluster.

## ONC Platform defaults

- IngressClass: nginx
- Default ingress class: true
- Service type: NodePort
- HTTP NodePort: 30080
- HTTPS NodePort: 30443

MetalLB can later change this to LoadBalancer.
