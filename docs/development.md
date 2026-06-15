# 🛠️ Guide de Développement local, Tests & Qualité de code

Ce document détaille la configuration de l'environnement de développement local, la gestion des dépendances et les outils de qualité de code (linters, testeurs, formateurs).

---

## 💻 Configuration de l'environnement local

### 1. Prérequis

Assurez-vous d'avoir Python 3.11+ et l'outil moderne de gestion de paquets Python `uv` installé sur votre machine.

#### Installer `uv` si nécessaire :
```bash
pip install uv
```

### 2. Installation des Dépendances

Synchronisez l'environnement virtuel local `.venv` à l'aide de `uv` :

```bash
# Pour installer uniquement les dépendances de production
uv sync

# Pour installer les dépendances de développement (tests, linters, etc.)
uv sync --all-extras
```

---

## 📦 Gestion des Dépendances

Le projet utilise `pyproject.toml` pour déclarer les dépendances et un fichier `uv.lock` figé pour garantir la reproductibilité.

> ⚠️ **Important :** Ne modifiez jamais manuellement le fichier `uv.lock`. Laissez les utilitaires `uv` s'en charger.

### Commandes utiles pour gérer les dépendances :
```bash
# Ajouter une dépendance de production
uv add <nom-du-package>

# Ajouter une dépendance optionnelle de développement
uv add --optional dev <nom-du-package>

# Supprimer une dépendance
uv remove <nom-du-package>
```

---

## ⚡ Démarrer l'API localement (Sans Docker)

Pour exécuter le serveur API localement en mode rechargement automatique (Hot Reload) :

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🧪 Validation & Qualité du Code

Avant de soumettre du code, veuillez exécuter les vérifications de qualité de code suivantes.

### 1. Exécuter la Suite de Tests
```bash
# Lancement des tests (unitaires & intégration)
uv run pytest tests/ -v

# Lancement des tests avec calcul de couverture et rapport HTML
uv run pytest tests/ -v --cov=app --cov-report=html
```

### 2. Formatage du Code (Black & Isort)
Le projet utilise `black` pour le formatage et `isort` pour le tri des imports.
```bash
# Vérifier si des fichiers nécessitent un formatage
uv run black --check app/ tests/

# Appliquer automatiquement le formatage Black
uv run black app/ tests/

# Trier les imports automatiquement
uv run isort app/ tests/
```

### 3. Analyse Statique & Linting (Pylint)
```bash
# Analyse du code avec Pylint
uv run pylint app/
```

### 4. Vérification du Typage (Mypy)
```bash
# Analyse de typage statique
uv run mypy app/ tests/
```
