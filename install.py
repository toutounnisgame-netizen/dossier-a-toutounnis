#!/usr/bin/env python3
"""
Script d'installation pour Windows
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Vérifie la version de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 ou supérieur est requis")
        print(f"   Version actuelle : {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor} détecté")
    return True

def check_ollama():
    """Vérifie si Ollama est installé"""
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        print("✅ Ollama détecté")
        return True
    except:
        print("⚠️  Ollama n'est pas installé")
        print("   Visitez https://ollama.ai pour l'installer")
        response = input("   Continuer quand même ? (y/n): ")
        return response.lower() == 'y'

def create_venv():
    """Crée l'environnement virtuel"""
    print("
🔧 Création de l'environnement virtuel...")
    subprocess.run([sys.executable, "-m", "venv", "venv"])
    print("✅ Environnement virtuel créé")

def install_dependencies():
    """Installe les dépendances"""
    print("
📦 Installation des dépendances...")

    # Déterminer le chemin pip selon l'OS
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")

    # Upgrade pip
    subprocess.run([pip_path, "install", "--upgrade", "pip"])

    # Installer requirements
    subprocess.run([pip_path, "install", "-r", "requirements.txt"])
    print("✅ Dépendances installées")

def create_directories():
    """Crée les dossiers nécessaires"""
    print("
📁 Création de la structure des dossiers...")
    dirs = [
        "data/memory/vectors",
        "data/logs",
        "data/exports"
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    print("✅ Dossiers créés")

def download_model():
    """Télécharge le modèle Ollama"""
    try:
        print("
🤖 Téléchargement du modèle Ollama...")
        subprocess.run(["ollama", "pull", "llama3.2"], check=True)
        print("✅ Modèle téléchargé")
    except:
        print("⚠️  Impossible de télécharger le modèle")
        print("   Exécutez manuellement : ollama pull llama3.2")

def main():
    """Installation principale"""
    print("════════════════════════════════════════════════════════════════════════")
    print("         ALMAA v2.0 - Installation du Système Multi-Agents")
    print("════════════════════════════════════════════════════════════════════════")
    print()

    # Vérifications
    if not check_python_version():
        return

    if not check_ollama():
        print("
⚠️  Installation continuée sans Ollama")

    # Installation
    create_venv()
    install_dependencies()
    create_directories()

    # Modèle Ollama
    if check_ollama():
        download_model()

    # Instructions finales
    print("
════════════════════════════════════════════════════════════════════════")
    print("                    ✅ Installation terminée !")
    print("════════════════════════════════════════════════════════════════════════")
    print("
Pour démarrer ALMAA :")

    if platform.system() == "Windows":
        print("  1. Activez l'environnement : venv\Scripts\activate")
    else:
        print("  1. Activez l'environnement : source venv/bin/activate")

    print("  2. Lancez ALMAA : python main.py interactive")
    print("
Pour plus d'aide : python main.py --help")

if __name__ == "__main__":
    main()
