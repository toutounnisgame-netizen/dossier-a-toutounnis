#!/usr/bin/env python3
"""Test rapide du système ALMAA"""

import sys
import time
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ALMAA
from loguru import logger

def test_basic_functionality():
    """Test les fonctionnalités de base"""

    logger.info("Starting ALMAA quick test...")

    # Initialiser
    almaa = ALMAA()

    # Tests
    tests = [
        ("Bonjour", "Salutation"),
        ("Crée une fonction pour calculer la factorielle", "Code Python"),
        ("Analyse ce code: def f(x): return x*2", "Analyse"),
    ]

    results = []

    for request, test_name in tests:
        logger.info(f"Test: {test_name}")
        logger.info(f"Request: {request}")

        start = time.time()
        result = almaa.process_request(request, timeout=10)
        duration = time.time() - start

        if result['success']:
            logger.success(f"✅ {test_name} - OK ({duration:.2f}s)")
            logger.info(f"Response: {result['response'][:100]}...")
        else:
            logger.error(f"❌ {test_name} - FAILED")
            logger.error(f"Error: {result['error']}")

        results.append({
            "test": test_name,
            "success": result['success'],
            "duration": duration
        })

        time.sleep(1)  # Pause entre tests

    # Résumé
    logger.info("\n" + "="*50)
    logger.info("RÉSUMÉ DES TESTS")
    logger.info("="*50)

    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)

    for r in results:
        status = "✅" if r['success'] else "❌"
        logger.info(f"{status} {r['test']} - {r['duration']:.2f}s")

    logger.info(f"\nTotal: {success_count}/{total_count} réussis")

    # Shutdown
    almaa.shutdown()

if __name__ == "__main__":
    test_basic_functionality()
