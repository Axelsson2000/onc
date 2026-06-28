# ONC Platform Installation Phases

## 01 - AlmaLinux Base

Clean AlmaLinux installation, updated OS, swap disabled, basic tools installed.

## 02 - Kubernetes Base

K3s single-node cluster installed with:

- Traefik disabled
- ServiceLB disabled
- kubeconfig configured for root

## 03 - GitOps Bootstrap

Argo CD installed manually. Root Application points to this Git repository.

## 04 - Platform

Argo CD deploys the platform layers from Git.

## 05 - Applications

Applications are deployed on top of the platform.
