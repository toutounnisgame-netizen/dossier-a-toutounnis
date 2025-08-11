#!/usr/bin/env python3
"""
Auto-fix handlers pour tous les agents ALMAA
Corrige les boucles de messages RESPONSE
"""

import os
from pathlib import Path

def main():
    """Apply all fixes automatically"""
    print("🛠️  CORRECTION HANDLERS ALMAA PHASE 2")
    print("=" * 60)
    
    # 1. Enhanced Chef
    print("\n1. Correction Enhanced Chef...")
    if Path("agents/enhanced_chef_fixed_handlers.py").exists():
        try:
            with open("agents/enhanced_chef_fixed_handlers.py", 'r', encoding='utf-8') as src:
                content = src.read()
            with open("agents/enhanced_chef.py", 'w', encoding='utf-8') as dst:
                dst.write(content)
            print("   ✅ Enhanced Chef corrigé")
        except Exception as e:
            print(f"   ❌ Erreur Enhanced Chef: {e}")
    else:
        print("   ⚠️  Fichier enhanced_chef_fixed_handlers.py non trouvé")
    
    # 2. Chef Projet
    print("\n2. Correction Chef Projet...")
    if Path("agents/chef_projet_fixed_handlers.py").exists():
        try:
            with open("agents/chef_projet_fixed_handlers.py", 'r', encoding='utf-8') as src:
                content = src.read()
            with open("agents/chef_projet.py", 'w', encoding='utf-8') as dst:
                dst.write(content)
            print("   ✅ Chef Projet corrigé")
        except Exception as e:
            print(f"   ❌ Erreur Chef Projet: {e}")
    else:
        print("   ⚠️  Fichier chef_projet_fixed_handlers.py non trouvé")
    
    # 3. Correction simple pour Memory Enhanced Worker
    print("\n3. Correction Memory Enhanced Worker...")
    try:
        if Path("agents/memory_enhanced_worker.py").exists():
            with open("agents/memory_enhanced_worker.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add RESPONSE handler
            if 'def handle_response(self, message: Message)' not in content:
                # Find the process_message method and add handlers
                response_handler = '''
    def handle_response(self, message: Message) -> Optional[Message]:
        """Handle RESPONSE messages to prevent loops"""
        logger.debug(f"{self.name} received RESPONSE from {message.sender}")
        return None
        
    def handle_error(self, message: Message) -> Optional[Message]:
        """Handle ERROR messages"""
        error_content = message.content.get("error", "Unknown error")
        logger.error(f"{self.name} received error from {message.sender}: {error_content}")
        return None
'''
                
                # Add handlers to message_handlers dict
                if '"RESPONSE": self.handle_response' not in content:
                    content = content.replace(
                        '"REQUEST_VOTE": self.handle_vote_request',
                        '"REQUEST_VOTE": self.handle_vote_request,\n            "RESPONSE": self.handle_response,\n            "ERROR": self.handle_error'
                    )
                    
                    # Add methods before the last method
                    content = content.replace(
                        'def get_stats(self):',
                        response_handler + '\n    def get_stats(self):'
                    )
                    
                with open("agents/memory_enhanced_worker.py", 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print("   ✅ Memory Enhanced Worker corrigé")
            else:
                print("   ➖ Memory Enhanced Worker déjà corrigé")
    except Exception as e:
        print(f"   ❌ Erreur Memory Enhanced Worker: {e}")
    
    print("\n🎯 CORRECTIONS APPLIQUÉES!")
    print("\nÉtapes suivantes:")
    print("1. python main_phase2.py interactive")
    print("2. Tester: 'Bonjour ALMAA'")
    print("3. Vérifier qu'il n'y a plus de boucles RESPONSE")

if __name__ == "__main__":
    main()