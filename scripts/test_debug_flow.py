#!/usr/bin/env python3
"""Test avec debug complet du flux de messages"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ALMAA
from core.base import Message
from loguru import logger

# Mode debug
logger.remove()
logger.add(sys.stdout, level="DEBUG")

def test_simple():
    """Test simple avec suivi détaillé"""

    logger.info("🚀 Test ALMAA - Suivi du flux de messages")

    almaa = ALMAA()

    # Test simple
    logger.info("\n" + "="*60)
    logger.info("📝 Test: Bonjour")
    logger.info("="*60)

    # Hook pour tracer les messages
    original_publish = almaa.bus.publish
    def traced_publish(message):
        logger.debug(f"📨 PUBLISH: {message.sender} → {message.recipient} ({message.type})")
        return original_publish(message)

    almaa.bus.publish = traced_publish

    # Envoyer la requête
    start_time = time.time()
    test_message = Message(
        sender="User",
        recipient="Chef",
        type="REQUEST",
        content={"request": "Bonjour"}
    )

    logger.info("📤 Envoi du message initial...")
    almaa.bus.publish(test_message)

    # Attendre et traiter
    timeout = 10
    response_found = False

    while time.time() - start_time < timeout:
        # Traiter les messages
        almaa.bus.process_agent_messages()

        # Vérifier l'agent User
        user_agent = almaa.agents.get("User")
        if user_agent and user_agent.inbox:
            for msg in user_agent.inbox:
                if msg.type == "RESPONSE":
                    logger.success(f"✅ Réponse trouvée: {msg.content}")
                    response_found = True
                    break

        if response_found:
            break

        time.sleep(0.1)

    if not response_found:
        logger.error("❌ Pas de réponse trouvée")

        # Debug
        logger.debug("\n🔍 État final:")
        for name, agent in almaa.agents.items():
            if agent.inbox or agent.outbox:
                logger.debug(f"{name}:")
                logger.debug(f"  Inbox: {len(agent.inbox)} messages")
                logger.debug(f"  Outbox: {len(agent.outbox)} messages")

        logger.debug(f"\n📜 Historique ({len(almaa.bus.message_history)} messages):")
        for msg in almaa.bus.message_history[-10:]:
            logger.debug(f"  {msg.sender} → {msg.recipient} ({msg.type})")

    almaa.shutdown()

if __name__ == "__main__":
    test_simple()
