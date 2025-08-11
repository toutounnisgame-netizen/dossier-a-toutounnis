#!/usr/bin/env python3
"""Debug détaillé ALMAA"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.chef import AgentChef
from loguru import logger
import json

def test_chef_responses():
    """Test les réponses du Chef"""
    
    chef = AgentChef()
    
    tests = [
        ("Bonjour", "Salutation simple"),
        ("Crée une fonction fibonacci", "Tâche de code"),
        ("Analyse ce code: x = 1", "Analyse"),
    ]
    
    for request, desc in tests:
        logger.info(f"\n📝 Test: {desc}")
        logger.info(f"   Request: {request}")
        
        try:
            result = chef.think({"user_request": request})
            if result:
                logger.success("✅ Réponse reçue:")
                logger.info(f"   Délégation: {result.get('délégation')}")
                logger.info(f"   Type: {result.get('type_tache')}")
                logger.info(f"   Complexité: {result.get('complexité')}")
                
                # Vérifier la délégation
                delegation = result.get('délégation', '')
                if delegation not in ['ChefProjet', 'moi-même']:
                    logger.error(f"❌ Délégation invalide: '{delegation}'")
            else:
                logger.error("❌ Pas de réponse")
                
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_chef_responses()
