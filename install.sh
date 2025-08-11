#!/bin/bash
# ALMAA v2.0 - Script d'installation automatique

echo "════════════════════════════════════════════════════════════════════════"
echo "         ALMAA v2.0 - Installation du Système Multi-Agents"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Vérifier Python
echo "🔍 Vérification des prérequis..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Veuillez installer Python 3.8 ou supérieur."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION détecté"

# Vérifier Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama n'est pas installé."
    echo "   Visitez https://ollama.ai pour l'installer."
    echo "   Continuez quand même ? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
else
    echo "✅ Ollama détecté"
fi

# Créer environnement virtuel
echo ""
echo "🔧 Création de l'environnement virtuel..."
python3 -m venv venv

# Activer environnement
echo "🔧 Activation de l'environnement..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Installer dépendances
echo ""
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Créer dossiers nécessaires
echo ""
echo "📁 Création de la structure des dossiers..."
mkdir -p data/{memory/vectors,logs,exports}

# Télécharger modèle Ollama si disponible
if command -v ollama &> /dev/null; then
    echo ""
    echo "🤖 Téléchargement du modèle Ollama (llama3.2)..."
    ollama pull llama3.2
fi

# Tests de base
echo ""
echo "🧪 Exécution des tests de base..."
python -m pytest tests/test_communication.py -v

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "                    ✅ Installation terminée !"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "Pour démarrer ALMAA :"
echo "  1. Activez l'environnement : source venv/bin/activate"
echo "  2. Lancez ALMAA : python main.py interactive"
echo ""
echo "Pour plus d'aide : python main.py --help"
echo ""
