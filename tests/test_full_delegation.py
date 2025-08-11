#!/usr/bin/env python3
"""Tests de la chaîne de délégation complète"""

import pytest
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ALMAA
from core.base import Message
from agents.special.philosophe import AgentPhilosophe
from loguru import logger

# Configuration pour les tests
logger.remove()
logger.add(sys.stdout, level="INFO")

class TestFullDelegation:
    """Tests de la délégation complète User → Chef → ChefProjet → Worker → User"""

    def setup_method(self):
        """Setup pour chaque test"""
        self.almaa = ALMAA()

        # Ajouter le Philosophe pour observer
        philosophe = AgentPhilosophe()
        self.almaa.register_agent(philosophe)

        # Hook pour tracer tous les messages
        self.message_trace = []
        original_publish = self.almaa.bus.publish

        def traced_publish(message):
            self.message_trace.append({
                "sender": message.sender,
                "recipient": message.recipient,
                "type": message.type,
                "timestamp": time.time()
            })
            logger.debug(f"📨 {message.sender} → {message.recipient} ({message.type})")
            return original_publish(message)

        self.almaa.bus.publish = traced_publish

    def teardown_method(self):
        """Cleanup après chaque test"""
        self.almaa.shutdown()

    def test_simple_code_generation(self):
        """Test : génération de code simple"""

        # Requête utilisateur
        result = self.almaa.process_request(
            "Crée une fonction Python pour calculer la factorielle",
            timeout=20
        )

        # Vérifications
        assert result['success'], f"Échec: {result.get('error')}"
        assert "def" in result['response'], "Pas de code Python dans la réponse"
        assert "factorial" in result['response'].lower() or "factorielle" in result['response'].lower()

        # Vérifier la chaîne de délégation
        self._verify_delegation_chain()

    def test_complex_task_delegation(self):
        """Test : tâche complexe nécessitant planification"""

        result = self.almaa.process_request(
            "Crée une API REST complète avec FastAPI pour gérer des todos",
            timeout=30
        )

        assert result['success']

        # Vérifier que ChefProjet a été impliqué
        chef_projet_messages = [
            m for m in self.message_trace 
            if m['sender'] == 'ChefProjet' or m['recipient'] == 'ChefProjet'
        ]
        assert len(chef_projet_messages) > 0, "ChefProjet n'a pas été impliqué"

    def test_error_handling(self):
        """Test : gestion des erreurs"""

        # Requête impossible
        result = self.almaa.process_request(
            "TÂCHE_IMPOSSIBLE_12345_!@#$%",
            timeout=10
        )

        # Devrait retourner une réponse, même en cas d'erreur
        assert 'response' in result or 'error' in result

    def test_philosophe_observation(self):
        """Test : le Philosophe observe correctement"""

        # Faire quelques requêtes
        for i in range(3):
            self.almaa.process_request(f"Test {i}", timeout=5)

        # Demander un rapport au Philosophe
        report_request = Message(
            sender="Test",
            recipient="Philosophe",
            type="REPORT_REQUEST",
            content={}
        )

        self.almaa.bus.publish(report_request)
        self.almaa.bus.process_agent_messages()

        # Vérifier que le Philosophe a observé
        philosophe = self.almaa.agents.get("Philosophe")
        assert philosophe is not None
        assert philosophe.metrics["total_messages"] > 0

        # Générer rapport
        report = philosophe.generate_report()
        assert report["period"]["total_messages"] > 0
        assert len(report["message_distribution"]) > 0

    def test_parallel_requests(self):
        """Test : requêtes parallèles"""

        import threading
        results = []

        def make_request(request_text):
            result = self.almaa.process_request(request_text, timeout=15)
            results.append(result)

        # Lancer 3 requêtes en parallèle
        threads = []
        requests = [
            "Crée une fonction pour trier une liste",
            "Génère une classe Person avec nom et âge",
            "Écris un script pour lire un fichier CSV"
        ]

        for req in requests:
            t = threading.Thread(target=make_request, args=(req,))
            threads.append(t)
            t.start()

        # Attendre que toutes finissent
        for t in threads:
            t.join()

        # Vérifier les résultats
        assert len(results) == 3
        success_count = sum(1 for r in results if r.get('success', False))
        assert success_count >= 2, f"Seulement {success_count}/3 requêtes réussies"

    def _verify_delegation_chain(self):
        """Vérifie que la chaîne de délégation est correcte"""

        # Extraire la séquence des messages
        chain = []
        for msg in self.message_trace:
            chain.append(f"{msg['sender']}→{msg['recipient']}")

        logger.info(f"Chaîne de délégation: {' | '.join(chain[:10])}")

        # Vérifications de base
        assert any("User→Chef" in c for c in chain), "User n'a pas contacté Chef"
        assert any("Chef→" in c for c in chain), "Chef n'a pas délégué"

def test_integration_scenarios():
    """Tests de scénarios d'intégration complets"""

    scenarios = [
        {
            "name": "Développement simple",
            "request": "Crée une fonction pour vérifier si un nombre est premier",
            "expected_in_response": ["def", "prime", "return"],
            "max_time": 15
        },
        {
            "name": "Analyse de code",
            "request": "Analyse ce code: def add(a, b): return a + b",
            "expected_in_response": ["fonction", "addition", "simple"],
            "max_time": 10
        },
        {
            "name": "Documentation",
            "request": "Génère la documentation pour une fonction de tri",
            "expected_in_response": ["Args:", "Returns:", "Example:"],
            "max_time": 12
        }
    ]

    almaa = ALMAA()
    failed = []

    for scenario in scenarios:
        logger.info(f"\n🧪 Test: {scenario['name']}")

        start = time.time()
        result = almaa.process_request(scenario["request"], timeout=scenario["max_time"])
        duration = time.time() - start

        if result.get('success'):
            response = result.get('response', '').lower()

            # Vérifier les éléments attendus
            missing = []
            for expected in scenario["expected_in_response"]:
                if expected.lower() not in response:
                    missing.append(expected)

            if missing:
                logger.warning(f"⚠️  Éléments manquants: {missing}")
                failed.append(scenario["name"])
            else:
                logger.success(f"✅ Succès en {duration:.1f}s")
        else:
            logger.error(f"❌ Échec: {result.get('error')}")
            failed.append(scenario["name"])

    almaa.shutdown()

    # Résumé
    logger.info(f"\n📊 Résumé: {len(scenarios) - len(failed)}/{len(scenarios)} réussis")

    if failed:
        logger.error(f"Échecs: {', '.join(failed)}")

    return len(failed) == 0

if __name__ == "__main__":
    # Lancer les tests
    logger.info("🚀 Tests de délégation complète ALMAA\n")

    # Tests unitaires avec pytest
    pytest.main([__file__, "-v", "--tb=short"])

    # Tests d'intégration
    logger.info("\n" + "="*60)
    logger.info("🧪 TESTS D'INTÉGRATION")
    logger.info("="*60)

    success = test_integration_scenarios()

    if success:
        logger.success("\n✅ Tous les tests sont passés!")
    else:
        logger.error("\n❌ Certains tests ont échoué")
        sys.exit(1)
