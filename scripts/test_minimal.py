#!/usr/bin/env python3
"""Test minimal pour vérifier le fix"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ALMAA
from loguru import logger

# Debug activé
logger.remove()
logger.add(sys.stdout, level="DEBUG")

def test_minimal():
    """Test le plus simple possible"""

    logger.info("🧪 Test minimal ALMAA")

    almaa = ALMAA()

    # Vérifier l'agent User
    user_agent = almaa.agents.get("User")
    logger.info(f"User agent trouvé: {user_agent is not None}")
    logger.info(f"User agent type: {type(user_agent).__name__}")

    # Test direct
    result = almaa.process_request("Bonjour", timeout=5)

    if result['success']:
        logger.success(f"✅ SUCCÈS: {result['response']}")
    else:
        logger.error(f"❌ ÉCHEC: {result['error']}")

        # Debug de l'état
        if user_agent:
            logger.debug(f"User inbox: {len(user_agent.inbox)} messages")
            for i, msg in enumerate(user_agent.inbox):
                logger.debug(f"  Message {i}: {msg.type} from {msg.sender}")
                if msg.type == "RESPONSE":
                    logger.warning(f"  → RESPONSE trouvée mais non récupérée!")

    almaa.shutdown()

if __name__ == "__main__":
    test_minimal()
