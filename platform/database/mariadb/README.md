# MariaDB

## Syfte

MariaDB är ONC-plattformens gemensamma databastjänst.

Komponenten installeras via Bitnamis Helm-chart och hanteras helt med GitOps genom Argo CD.

---

# Arkitektur

Git
↓
Argo CD
↓
Bitnami Helm Chart
↓
StatefulSet
↓
PersistentVolumeClaim
↓
Longhorn

---

# Konfiguration

| Parameter | Värde |
|----------|--------|
| Chart | Bitnami MariaDB |
| Version | 23.0.4 |
| Arkitektur | Standalone |
| StorageClass | Longhorn |
| Diskstorlek | 10 GiB |
| Databas | nextcloud |
| Autentisering | existingSecret |

---

# Secrets

Lösenord lagras inte i values.yaml.

Istället används ett Kubernetes Secret.

Secret:

    mariadb-secret

Det följer ONC:s arkitekturprincip:

- Secrets skall inte ligga i Helm values.

---

# GitOps

MariaDB installeras via Argo CD Multiple Sources.

Helm-chart hämtas från Bitnami.

Konfiguration hämtas från Git.

Flödet ser ut så här:

Bitnami Helm Chart
        +
Git values.yaml
        ↓
     Argo CD
        ↓
    Kubernetes

---

# Argo CD och StatefulSet

MariaDB använder ett StatefulSet.

Efter att StatefulSet skapats modifierar Kubernetes och Helm vissa fält automatiskt.

Exempel:

- spec.volumeClaimTemplates[].status
- spec.template.metadata.annotations["checksum/configuration"]

Dessa värden representerar inte användarkonfiguration utan genereras automatiskt av Kubernetes eller Helm.

Argo CD jämför alltid önskat tillstånd (Git) med faktiskt tillstånd (Kubernetes).

Resultatet blev initialt:

Healthy
OutOfSync

trots att:

- Pod körde
- PVC fungerade
- Longhorn fungerade
- Databasen gick att ansluta till
- Nextcloud-databasen skapades korrekt

För att undvika falska OutOfSync används därför ignoreDifferences endast för dessa Kubernetes-genererade fält.

Det gör att:

- verkliga konfigurationsändringar fortfarande upptäcks
- Kubernetes-genererade värden ignoreras
- Git fortsätter vara sanningen

---

# Designbeslut

## Varför Standalone?

ONC är för närvarande en utvecklings- och labbplattform.

Standalone ger:

- enklare drift
- lägre resursförbrukning
- enklare felsökning

Galera eller repliker kan införas senare vid behov.

---

## Varför Longhorn?

Longhorn används eftersom det ger:

- Persistent Storage
- Snapshot
- Backup
- Restore
- GitOps-kompatibilitet

---

## Varför existingSecret?

Lösenord skall inte ligga i Git som Helm-konfiguration.

All autentisering hanteras via Kubernetes Secrets.

Det gör det möjligt att senare ersätta Secrets med exempelvis:

- External Secrets
- HashiCorp Vault
- annan central Secret-hantering

utan att Helm-konfigurationen behöver ändras.

---

# Gate

MariaDB betraktas som godkänd när följande kriterier är uppfyllda:

- Argo CD visar Healthy
- Argo CD visar Synced
- Pod är Running
- PVC är Bound
- Longhorn-volym är Healthy
- Databasen kan nås
- Databas kan skapas
- Databasen kan användas av andra komponenter

---

# Drift

## Kontrollera status

kubectl get application platform-database-mariadb -n argocd

kubectl get pods -n platform-database

kubectl get pvc -n platform-database

---

# Felsökning

Om Argo CD visar:

Healthy
OutOfSync

kontrollera först om skillnaden endast består av Kubernetes-genererade StatefulSet-fält.

Det är vanligt för Helm-baserade StatefulSets och innebär inte nödvändigtvis att komponenten är felaktig.

---

# ONC-principer

MariaDB följer ONC:s arkitekturprinciper:

- Git är sanningen
- GitOps används för all konfiguration
- Secrets lagras inte i values.yaml
- En komponent = en katalog
- Minsta möjliga ignoreDifferences används
- Plattformen byggs lager för lager
- Komponenten måste klara sin Gate innan nästa lager byggs
