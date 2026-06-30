# MariaDB

## Syfte

MariaDB utgör ONC-plattformens databaslager.

Komponenten är tänkt att användas av applikationer som behöver en relationsdatabas, till exempel Nextcloud.

MariaDB installeras via Bitnamis Helm-chart och hanteras av Argo CD enligt ONC:s GitOps-principer.

---

## Arkitektur

Flödet är:

Git
  -> Argo CD
  -> Bitnami Helm Chart
  -> StatefulSet
  -> PersistentVolumeClaim
  -> Longhorn

MariaDB körs som ett StatefulSet med persistent lagring i Longhorn.

---

## Katalogstruktur

Komponenten ligger här:

platform/database/mariadb/

Viktiga filer:

- application.yaml
- values.yaml
- README.md
- kustomization.yaml
- resources/kustomization.yaml
- resources/secret.yaml

---

## Konfiguration

Helm-chart:

- Repository: https://charts.bitnami.com/bitnami
- Chart: mariadb
- Version: 23.0.4

Deployment:

- Architecture: standalone
- Namespace: platform-database
- Application name: platform-database-mariadb

Lagring:

- StorageClass: longhorn
- Storlek: 10Gi
- Access mode: ReadWriteOnce

Databas:

- Database: nextcloud
- Username: nextcloud

Autentisering:

- existingSecret: mariadb-secret

---

## Secrets

Lösenord ska inte ligga öppet i values.yaml.

MariaDB använder därför ett Kubernetes Secret:

mariadb-secret

Secretet innehåller:

- mariadb-root-password
- mariadb-password

I nuläget ligger detta som ett Kubernetes Secret i Git för labbsyfte.

På sikt kan detta ersättas av exempelvis:

- External Secrets
- HashiCorp Vault
- annan central secret-hantering

Det viktiga designbeslutet är att Helm values inte innehåller lösenord.

---

## GitOps

MariaDB installeras via Argo CD Multiple Sources.

Chart hämtas från Bitnami.

Values hämtas från Git.

Det innebär:

- Git äger konfigurationen.
- Argo CD renderar chartet.
- Kubernetes kör resultatet.
- Manuella ändringar i klustret ska undvikas.

Normalt flöde:

Git commit
  -> Git push
  -> Argo CD sync
  -> Kubernetes uppdateras

---

## Argo CD OutOfSync-problemet

### Bakgrund

Efter installation av MariaDB uppstod ett tillstånd där applikationen fungerade men Argo CD ändå visade:

Healthy
OutOfSync

Detta var missvisande eftersom MariaDB faktiskt fungerade.

Verifierat fungerade:

- Podden startade.
- StatefulSet var Healthy.
- PVC skapades.
- Longhorn-volymen var Healthy.
- MariaDB accepterade anslutningar.
- Databasen kunde användas.

Problemet låg alltså inte i MariaDB, Longhorn eller databasen.

---

## Felsökning

Felsökningen gjordes stegvis enligt ONC-principen att felsöka lager för lager.

Kontroller som gjordes:

- kubectl get application platform-database-mariadb -n argocd
- kubectl get pods -n platform-database
- kubectl get pvc -n platform-database
- kubectl logs platform-database-mariadb-0 -n platform-database
- argocd app diff platform-database-mariadb
- argocd app manifests platform-database-mariadb
- kubectl get statefulset platform-database-mariadb -n platform-database -o yaml

Argo CD CLI installerades på servern för att kunna analysera diff direkt i terminalen.

---

## Verklig orsak

Den verkliga diffen låg i StatefulSetets volumeClaimTemplates.

Helm renderade fältet så här:

volumeClaimTemplates:
- apiVersion: v1
  kind: PersistentVolumeClaim
  metadata:
    name: data

Men Kubernetes lagrade objektet så här:

volumeClaimTemplates:
- metadata:
    name: data

Kubernetes tog alltså bort dessa två fält:

- apiVersion
- kind

Detta sker eftersom de är redundanta inne i StatefulSetets volumeClaimTemplates.

Argo CD jämför Git/Helm-renderat manifest mot Kubernetes live-objekt.

Eftersom Helm renderade apiVersion och kind, men Kubernetes inte lagrade dem, blev applikationen permanent OutOfSync trots att allt fungerade.

---

## Lösning

Lösningen blev att lägga till ignoreDifferences på exakt de två fält som Kubernetes tar bort.

I application.yaml används:

ignoreDifferences:
  - group: apps
    kind: StatefulSet
    name: platform-database-mariadb
    namespace: platform-database
    jsonPointers:
      - /spec/volumeClaimTemplates/0/apiVersion
      - /spec/volumeClaimTemplates/0/kind

Dessutom används:

syncOptions:
  - CreateNamespace=true
  - RespectIgnoreDifferences=true

Efter denna ändring blev MariaDB:

Healthy
Synced

---

## Viktig lärdom

Detta var inte ett fel i:

- MariaDB
- Longhorn
- Kubernetes
- Helm-chartets funktion
- databasen

Det var en skillnad mellan:

- hur Helm renderar StatefulSetet
- hur Kubernetes normaliserar och lagrar StatefulSetet
- hur Argo CD jämför önskat och faktiskt tillstånd

---

## ONC-princip för ignoreDifferences

ignoreDifferences ska användas restriktivt.

Vi ignorerar inte hela StatefulSetet.

Vi ignorerar inte hela volumeClaimTemplates.

Vi ignorerar endast de exakta fält som Kubernetes själv tar bort:

- /spec/volumeClaimTemplates/0/apiVersion
- /spec/volumeClaimTemplates/0/kind

Detta gör att Argo CD fortfarande upptäcker riktiga konfigurationsändringar.

---

## ServerSideApply

ServerSideApply testades under felsökningen.

Beteendet kvarstod även efter att ServerSideApply togs bort från MariaDB-applikationen.

För MariaDB används därför inte ServerSideApply just nu.

Detta är ett medvetet komponentundantag.

ONC:s princip är:

- ServerSideApply kan användas där det fungerar bra.
- Komponenter får undantag om det finns tydlig teknisk orsak.
- Undantag ska dokumenteras.

---

## Gate

MariaDB betraktas som godkänd när följande är uppfyllt:

- Argo CD visar Healthy.
- Argo CD visar Synced.
- StatefulSet är Healthy.
- Podden är Running.
- PVC är Bound.
- Longhorn-volymen är Healthy.
- MariaDB accepterar anslutningar.
- Applikationer kan använda databasen.

Aktuell status efter åtgärd:

- Healthy: ja
- Synced: ja

---

## Driftkommandon

Kontrollera Argo CD-status:

kubectl get application platform-database-mariadb -n argocd

Kontrollera pod:

kubectl get pods -n platform-database

Kontrollera PVC:

kubectl get pvc -n platform-database

Kontrollera loggar:

kubectl logs platform-database-mariadb-0 -n platform-database

Kontrollera Argo diff:

argocd app diff platform-database-mariadb

Kontrollera renderade manifest:

argocd app manifests platform-database-mariadb

---

## Designbeslut

MariaDB körs som standalone eftersom ONC i nuläget är en labb- och utvecklingsplattform.

Longhorn används för persistent lagring.

Secrets hålls utanför values.yaml.

Argo CD Multiple Sources används för Helm-baserade komponenter.

ignoreDifferences används endast för kända Kubernetes-normaliserade fält.

---

## Sammanfattning

MariaDB är nu korrekt installerad och GitOps-kompatibel i ONC.

Det tidigare OutOfSync-problemet berodde på att Kubernetes normaliserade bort apiVersion och kind från volumeClaimTemplates.

Genom att ignorera exakt dessa två fält blev MariaDB Healthy och Synced utan att dölja verkliga konfigurationsändringar.
