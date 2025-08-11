# GUIDE D'INSTALLATION DÉTAILLÉ - ALMAA v2.0

## 🚀 Installation Rapide (Recommandée)

### Linux/Mac
```bash
chmod +x install.sh
./install.sh
```

### Windows
```powershell
# Ouvrir PowerShell en tant qu'administrateur
python install.py
```

## 📋 Installation Manuelle Étape par Étape

### 1. Prérequis Système

#### Python
- Version minimum : Python 3.8
- Vérifier : `python3 --version`
- Installer : https://www.python.org/downloads/

#### Ollama
- Requis pour les modèles LLM locaux
- Installer : https://ollama.ai/download
- Vérifier : `ollama --version`
- Télécharger le modèle : `ollama pull llama3.2`

### 2. Préparation de l'Environnement

```bash
# Extraire l'archive
unzip almaa-v2.0.zip
cd almaa-v2.0

# Créer environnement virtuel
python3 -m venv venv

# Activer l'environnement
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Mettre à jour pip
pip install --upgrade pip
```

### 3. Installation des Dépendances

```bash
# Installer toutes les dépendances
pip install -r requirements.txt

# Si erreurs avec ChromaDB sur Mac M1/M2
pip install --upgrade --force-reinstall chromadb

# Si erreurs avec sentence-transformers
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 4. Configuration Initiale

```bash
# Créer les dossiers nécessaires
mkdir -p data/{memory/vectors,logs,exports}

# Copier la configuration par défaut
cp config/default.yaml config/local.yaml

# Éditer si nécessaire
nano config/local.yaml  # ou votre éditeur préféré
```

### 5. Vérification de l'Installation

```bash
# Test rapide
python scripts/quick_test.py

# Si succès, vous verrez :
# ✅ Salutation - OK
# ✅ Code Python - OK
# ✅ Analyse - OK
```

## 🔧 Résolution des Problèmes

### Erreur : "ollama: command not found"
```bash
# Vérifier si Ollama est dans le PATH
which ollama

# Si non, ajouter au PATH (Linux/Mac)
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.bashrc
source ~/.bashrc
```

### Erreur : "ModuleNotFoundError"
```bash
# Vérifier que l'environnement virtuel est activé
which python  # Doit pointer vers venv/bin/python

# Réinstaller les dépendances
pip install --force-reinstall -r requirements.txt
```

### Erreur : "Connection refused" avec Ollama
```bash
# Vérifier qu'Ollama est lancé
ollama serve

# Dans un autre terminal, tester
ollama list
```

### Performance lente
1. Réduire le modèle : Éditer `config/default.yaml`
   ```yaml
   agents:
     default_model: "llama2:7b"  # Plus petit que llama3.2
   ```

2. Augmenter le timeout :
   ```yaml
   agents:
     timeout: 60  # Au lieu de 30
   ```

## 📊 Configuration Avancée

### Modèles Ollama Recommandés
- **llama3.2** : Meilleur équilibre performance/qualité (par défaut)
- **llama2:7b** : Plus rapide, moins précis
- **codellama:7b** : Optimisé pour le code
- **mistral:7b** : Alternative performante

### Optimisation Mémoire
Pour machines avec peu de RAM (< 8GB) :
```yaml
# config/local.yaml
memory:
  max_size: 100000  # Réduire de 1000000
  compression_threshold: 0.7  # Plus agressif

agents:
  max_agents: 10  # Réduire de 20
```

## 🚀 Premiers Pas

### 1. Lancer ALMAA
```bash
python main.py interactive
```

### 2. Commandes de Base
- **Aide** : `/help`
- **Statut** : `/status`
- **Agents** : `/agents`
- **Quitter** : `exit`

### 3. Exemples de Requêtes
```
Vous> Crée une fonction Python pour trier une liste
Vous> Analyse les performances de ce code: [votre code]
Vous> Comment optimiser une base de données SQL?
```

## 📝 Checklist Post-Installation

- [ ] Python 3.8+ installé
- [ ] Ollama installé et modèle téléchargé
- [ ] Environnement virtuel créé et activé
- [ ] Dépendances installées sans erreur
- [ ] Tests rapides passés
- [ ] Premier lancement réussi

## 🆘 Support

Si vous rencontrez des problèmes :
1. Vérifier les logs : `cat data/logs/almaa.log`
2. Mode debug : Éditer `config/local.yaml` → `debug: true`
3. Consulter la documentation : `docs/troubleshooting.md`

---

Bon développement avec ALMAA ! 🎉
