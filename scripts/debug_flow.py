#!/usr/bin/env python3
"""Script de debug pour ALMAA"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ALMAA
from core.base import Message
from loguru import logger

def debug_flow():
    logger.info("🔍 Debug ALMAA...")
    
    almaa = ALMAA()
    
    # Test simple
    logger.info("📤 Envoi requête...")
    result = almaa.process_request("Bonjour", timeout=15)
    
    if result['success']:
        logger.success(f"✅ Réponse: {result['response']}")
    else:
        logger.error(f"❌ Erreur: {result['error']}")
        
        # Debug détaillé
        logger.info("\n📊 État des agents:")
        for name, agent in almaa.agents.items():
            logger.info(f"  {name}: {len(agent.inbox)} messages")
            for msg in agent.inbox:
                logger.info(f"    - {msg.type} from {msg.sender}")
    
    almaa.shutdown()

if __name__ == "__main__":
    debug_flow()
