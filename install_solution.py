#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'installation automatique pour ALMAA v2.0 Complete Solution
Vérifie et installe toutes les dépendances nécessaires
"""
import sys
import subprocess
import importlib
import os
from pathlib import Path


def check_python_version():
    """Vérifie la version de Python"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")
    return True


def check_virtual_env():
    """Vérifie si on est dans un environnement virtuel"""
    print("📦 Checking virtual environment...")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  No virtual environment detected (recommended)")
        return True  # Pas obligatoire mais recommandé


def install_package(package_name, import_name=None):
    """Installe un package si nécessaire"""
    if import_name is None:
        import_name = package_name.split('==')[0].split('>=')[0].split('[')[0]
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {import_name} already installed")
        return True
    except ImportError:
        print(f"📥 Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ {package_name} installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package_name}: {e}")
            return False


def install_dependencies():
    """Installe toutes les dépendances"""
    print("📦 Installing dependencies...")
    
    # Core dependencies
    dependencies = [
        ("pydantic>=2.0.0", "pydantic"),
        ("click>=8.0.0", "click"),
        ("pyyaml>=6.0.0", "yaml"),
        ("python-dotenv>=1.0.0", "dotenv"),
        ("loguru>=0.7.0", "loguru"),
        ("uuid", None),  # Built-in, skip
        ("typing", None),  # Built-in, skip
        ("datetime", None),  # Built-in, skip
        ("threading", None),  # Built-in, skip
        ("collections", None),  # Built-in, skip
        ("queue", None),  # Built-in, skip
        ("pathlib", None),  # Built-in, skip
    ]
    
    # AI/ML dependencies (optional)
    optional_dependencies = [
        ("ollama>=0.1.7", "ollama"),
        ("chromadb>=0.4.0", "chromadb"),
        ("sentence-transformers>=2.2.0", "sentence_transformers"),
        ("numpy>=1.24.0", "numpy"),
        ("scikit-learn>=1.3.0", "sklearn"),
    ]
    
    # Dev dependencies
    dev_dependencies = [
        ("pytest>=7.4.0", "pytest"),
        ("pytest-asyncio>=0.21.0", None),  # Skip import check
    ]
    
    all_success = True
    
    # Install core
    print("\n🔧 Installing core dependencies...")
    for package, import_name in dependencies:
        if import_name is not None:
            if not install_package(package, import_name):
                all_success = False
    
    # Install optional (avec gestion d'erreur)
    print("\n🤖 Installing AI/ML dependencies...")
    for package, import_name in optional_dependencies:
        try:
            if not install_package(package, import_name):
                print(f"⚠️  Optional dependency {package} failed, continuing...")
        except Exception as e:
            print(f"⚠️  Error with {package}: {e}")
    
    # Install dev (optionnel)
    print("\n🧪 Installing development dependencies...")
    for package, import_name in dev_dependencies:
        try:
            install_package(package, import_name)
        except Exception as e:
            print(f"⚠️  Dev dependency {package} failed: {e}")
    
    return all_success


def check_ollama():
    """Vérifie si Ollama est disponible"""
    print("🤖 Checking Ollama availability...")
    
    try:
        import ollama
        # Test simple
        models = ollama.list()
        print("✅ Ollama is available and running")
        
        # Vérifier si llama3.2 est disponible
        model_names = [model['name'] for model in models.get('models', [])]
        if any('llama3.2' in name for name in model_names):
            print("✅ llama3.2 model found")
        else:
            print("⚠️  llama3.2 model not found, you may need to pull it:")
            print("   ollama pull llama3.2")
        
        return True
    except ImportError:
        print("❌ Ollama Python client not installed")
        return False
    except Exception as e:
        print(f"⚠️  Ollama connection issue: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return True  # Continue anyway


def check_file_structure():
    """Vérifie la structure des fichiers"""
    print("📁 Checking file structure...")
    
    required_files = [
        "core/response_manager.py",
        "core/enhanced_messagebus.py", 
        "agents/user_response_collector.py",
        "main_complete.py",
        "tests/test_response_flow.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ All required files present")
        return True


def create_directories():
    """Crée les répertoires nécessaires"""
    print("📁 Creating necessary directories...")
    
    directories = [
        "data/logs",
        "data/memory/vectors",
        "data/exports"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/verified: {directory}")


def run_basic_test():
    """Lance un test basique"""
    print("🧪 Running basic test...")
    
    try:
        # Test d'import
        sys.path.insert(0, str(Path.cwd()))
        
        from core.response_manager import ResponseManager
        from core.enhanced_messagebus import EnhancedMessageBus
        from agents.user_response_collector import UserResponseCollector
        
        # Test création
        manager = ResponseManager()
        bus = EnhancedMessageBus(manager)
        collector = UserResponseCollector(manager)
        
        print("✅ Basic imports and creation successful")
        
        # Cleanup
        manager.shutdown()
        bus.stop()
        
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False


def main():
    """Installation principale"""
    print("🚀 ALMAA v2.0 Complete Solution - Installation")
    print("=" * 60)
    
    success = True
    
    # Vérifications
    if not check_python_version():
        success = False
    
    check_virtual_env()
    
    if not check_file_structure():
        print("\n❌ File structure check failed!")
        print("Make sure you've extracted all files from the ZIP")
        success = False
    
    # Installation
    if success and not install_dependencies():
        print("\n❌ Dependency installation failed!")
        success = False
    
    # Vérifications post-installation
    if success:
        create_directories()
        check_ollama()
        
        if not run_basic_test():
            success = False
    
    # Résultat final
    print("\n" + "=" * 60)
    if success:
        print("✅ INSTALLATION SUCCESSFUL!")
        print("\n🚀 Ready to use ALMAA v2.0 Complete:")
        print("   python main_complete.py interactive")
        print("\n📚 See README_SOLUTION.md for detailed usage")
    else:
        print("❌ INSTALLATION FAILED!")
        print("\n🔧 Please check the errors above and retry")
        print("   You may need to install dependencies manually")
    
    return success


if __name__ == "__main__":
    exit(0 if main() else 1)