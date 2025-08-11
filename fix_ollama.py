#!/usr/bin/env python3
"""
Fix Ollama imports in all ALMAA agents
Auto-correction pour le problème de connexion Ollama
"""

import os
from pathlib import Path
import re

def fix_ollama_imports():
    """Fix ollama imports in all agent files"""
    
    files_to_fix = [
        "agents/chef.py",
        "agents/chef_projet.py", 
        "agents/enhanced_chef.py",
        "agents/memory_enhanced_worker.py",
        "agents/mixins/debater.py",
        "agents/special/moderator.py"
    ]
    
    print("🛠️  CORRECTION AUTOMATIQUE DES IMPORTS OLLAMA")
    print("=" * 60)
    
    for file_path in files_to_fix:
        if not Path(file_path).exists():
            print(f"⚠️  Fichier non trouvé: {file_path}")
            continue
            
        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace import
            content = content.replace(
                "import ollama", 
                "from core.ollama_client import generate"
            )
            
            # Replace usage
            content = content.replace("ollama.generate(", "generate(")
            
            # Check if changes were made
            if content != original_content:
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ Corrigé: {file_path}")
            else:
                print(f"➖ Pas de changement: {file_path}")
                
        except Exception as e:
            print(f"❌ Erreur sur {file_path}: {e}")
    
    print("\n🎯 ÉTAPE SUIVANTE:")
    print("1. Vérifier que core/ollama_client.py existe")
    print("2. Lancer: python main_phase2.py interactive")
    print("3. Tester: 'Bonjour ALMAA'")

def verify_ollama_client():
    """Verify ollama client exists"""
    client_path = Path("core/ollama_client.py")
    
    if client_path.exists():
        print("✅ core/ollama_client.py trouvé")
        return True
    else:
        print("❌ core/ollama_client.py manquant")
        print("   Vous devez d'abord créer ce fichier!")
        return False

def main():
    """Main correction process"""
    print("🔧 CORRECTIF OLLAMA POUR ALMAA PHASE 2")
    print("=" * 50)
    
    # Check if ollama client exists
    if not verify_ollama_client():
        print("\n💡 CRÉER D'ABORD:")
        print("   core/ollama_client.py (fourni dans les fichiers)")
        return
    
    # Apply fixes
    fix_ollama_imports()
    
    print("\n🧪 TEST RECOMMANDÉ:")
    print("python -c \"from core.ollama_client import generate; print('Import OK')\"")

if __name__ == "__main__":
    main()