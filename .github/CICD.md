# CI/CD Configuration Guide

Ce document explique la configuration CI/CD mise en place avec GitHub Actions pour le projet WooOdooConnector.

## Vue d'ensemble

Le projet utilise plusieurs workflows GitHub Actions pour automatiser les tests, la construction d'images Docker, l'analyse de sécurité et le déploiement.

### Workflows disponibles

1. **CI** (`.github/workflows/ci.yml`) - Tests et qualité de code
2. **Docker Build** (`.github/workflows/docker.yml`) - Construction d'images Docker
3. **Coverage** (`.github/workflows/coverage.yml`) - Couverture de code
4. **Deploy** (`.github/workflows/deploy.yml`) - Déploiement (manuel)

---

## 1. Workflow CI

**Déclencheurs:**
- Push sur `main` ou `develop`
- Pull requests vers `main` ou `develop`

**Jobs:**

### Test Job
- Teste le code sur Python 3.11 et 3.12
- Installe les dépendances depuis `requirements.txt`
- Exécute pytest avec verbose output

### Lint Job
- Vérifie la qualité du code avec `flake8`
- Vérifie le formatage avec `black`

### Security Job
- Analyse les vulnérabilités avec `bandit`
- Vérifie les dépendances avec `safety`

**Configuration requise:**
Aucune - fonctionne out of the box

---

## 2. Workflow Docker Build

**Déclencheurs:**
- Push sur `main`
- Tags `v*.*.*` (releases)
- Pull requests vers `main`

**Fonctionnalités:**
- Build de l'image Docker
- Push vers GitHub Container Registry (ghcr.io)
- Cache des layers Docker pour builds rapides
- Scan de sécurité avec Trivy
- Tagging automatique basé sur git

**Configuration requise:**

1. Activer GitHub Container Registry:
   - Allez dans Settings > Actions > General
   - Sous "Workflow permissions", sélectionnez "Read and write permissions"

2. L'image sera disponible à: `ghcr.io/<username>/wooodooconnector`

**Utilisation de l'image:**

```bash
# Pull l'image
docker pull ghcr.io/<username>/wooodooconnector:main

# Run l'image
docker run -p 8000:8000 --env-file .env ghcr.io/<username>/wooodooconnector:main
```

---

## 3. Workflow Coverage

**Déclencheurs:**
- Push sur `main` ou `develop`
- Pull requests vers `main` ou `develop`

**Fonctionnalités:**
- Génère un rapport de couverture de code
- Upload vers Codecov (optionnel)
- Crée des artifacts avec les rapports HTML
- Commente les PRs avec les statistiques de couverture

**Configuration optionnelle:**

Pour utiliser Codecov:
1. Créez un compte sur [codecov.io](https://codecov.io)
2. Ajoutez votre repository
3. Ajoutez le token dans GitHub Secrets:
   - Settings > Secrets and variables > Actions
   - Nouveau secret: `CODECOV_TOKEN`

---

## 4. Workflow Deploy

**Déclencheurs:**
- Manuel (workflow_dispatch) par défaut
- Peut être activé pour push/release (commenté)

**Options de déploiement:**

### Option 1: SSH Deployment (par défaut)

Configure les secrets suivants:
- `DEPLOY_HOST`: Hostname du serveur
- `DEPLOY_USER`: Nom d'utilisateur SSH
- `DEPLOY_SSH_KEY`: Clé SSH privée

```bash
# Générer une clé SSH si nécessaire
ssh-keygen -t ed25519 -C "github-actions"
# Copier la clé publique sur le serveur
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server
# Copier la clé privée dans GitHub Secrets
```

### Option 2: Docker Swarm

Décommentez la section Docker Swarm et configurez:
- `SWARM_MANAGER_HOST`
- `SWARM_USER`
- `SWARM_SSH_KEY`

### Option 3: Kubernetes

Décommentez la section Kubernetes et ajoutez les manifests k8s.

**Déclenchement manuel:**

1. Allez dans Actions > Deploy
2. Click "Run workflow"
3. Sélectionnez l'environnement (staging/production)
4. Click "Run workflow"

---

## Configuration des Secrets GitHub

Pour configurer les secrets:

1. Allez dans votre repository sur GitHub
2. Settings > Secrets and variables > Actions
3. Click "New repository secret"

### Secrets recommandés:

```
DEPLOY_HOST=your-server.com
DEPLOY_USER=deploy
DEPLOY_SSH_KEY=<private-key-content>
CODECOV_TOKEN=<codecov-token>
```

---

## Environments

Pour utiliser les environments (staging/production):

1. Settings > Environments
2. Créez "staging" et "production"
3. Configurez les protection rules:
   - Production: Require reviewers
   - Production: Wait timer (optionnel)
4. Ajoutez des secrets spécifiques par environment

---

## Badges pour README

Ajoutez ces badges dans votre README.md:

```markdown
![CI](https://github.com/<username>/WooOdooConnector/workflows/CI/badge.svg)
![Docker Build](https://github.com/<username>/WooOdooConnector/workflows/Docker%20Build/badge.svg)
![Coverage](https://codecov.io/gh/<username>/WooOdooConnector/branch/main/graph/badge.svg)
```

---

## Optimisations et bonnes pratiques

### 1. Cache des dépendances

Les workflows utilisent déjà le cache pip:
```yaml
uses: actions/setup-python@v5
with:
  cache: 'pip'
```

### 2. Matrix builds

Le workflow CI teste sur Python 3.11 et 3.12:
```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']
```

### 3. Parallel jobs

Les jobs `test`, `lint` et `security` s'exécutent en parallèle.

### 4. Conditional execution

Les push d'images Docker se font uniquement sur push (pas sur PR):
```yaml
if: github.event_name != 'pull_request'
```

---

## Personnalisation

### Ajouter des notifications

Ajoutez dans le workflow deploy:

```yaml
- name: Notify Slack
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Deployment completed'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
  if: always()
```

### Ajouter des tests d'intégration

Créez un nouveau workflow `.github/workflows/integration.yml`:

```yaml
name: Integration Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: |
          docker-compose up -d
          pytest tests/integration/
          docker-compose down
```

### Déploiement automatique

Pour activer le déploiement auto sur push:

Dans `.github/workflows/deploy.yml`, décommentez:
```yaml
on:
  push:
    branches: [ main ]
```

---

## Dépannage

### Les tests échouent

1. Vérifiez les logs dans Actions > CI
2. Reproduisez localement:
   ```bash
   pytest -v
   ```

### Docker build échoue

1. Testez le build localement:
   ```bash
   docker build -f docker/Dockerfile -t test .
   ```

### Permissions Docker push

Vérifiez que "Read and write permissions" est activé dans:
Settings > Actions > General > Workflow permissions

### SSH deployment fails

1. Vérifiez que la clé SSH est correcte
2. Testez la connexion manuellement:
   ```bash
   ssh -i <key> user@host
   ```

---

## Monitoring

### Voir les workflows en cours

```bash
gh run list
gh run view <run-id>
gh run watch
```

### Télécharger les artifacts

```bash
gh run download <run-id>
```

---

## Coûts GitHub Actions

- Public repos: GitHub Actions est gratuit
- Private repos: 2000 minutes/mois gratuites
- Les workflows actuels consomment ~5-10 min par run

**Estimation:**
- 50 commits/mois = ~500 minutes
- Reste dans le quota gratuit

Pour optimiser:
- Utilisez le cache efficacement
- Limitez les matrix builds si nécessaire
- Utilisez `paths` pour ne trigger que sur certains fichiers

---

## Prochaines étapes

1. Testez les workflows en faisant un push
2. Configurez Codecov si souhaité
3. Configurez les secrets de déploiement
4. Ajoutez les badges dans le README
5. Personnalisez selon vos besoins

---

## Support

Pour toute question:
- GitHub Discussions
- Issues GitHub
- Documentation: https://docs.github.com/actions
