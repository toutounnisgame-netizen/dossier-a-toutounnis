#!/usr/bin/env python3
"""Test complet avec tous les cas"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ALMAA
from loguru import logger

def test_complete():
    """Test complet ALMAA"""

    logger.info("🚀 Test complet ALMAA v2.0...")

    almaa = ALMAA()

    tests = [
        ("Bonjour", "Salutation"),
        ("Crée une fonction Python pour calculer fibonacci", "Code Python"),
        ("Analyse ce code: def f(x): return x*2", "Analyse"),
    ]

    results = []

    for request, test_name in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"📝 Test: {test_name}")
        logger.info(f"📤 Request: {request}")
        logger.info(f"{'='*60}")

        start_time = time.time()
        result = almaa.process_request(request, timeout=15)
        duration = time.time() - start_time

        if result['success']:
            logger.success(f"✅ {test_name} - OK ({duration:.2f}s)")
            logger.info(f"📥 Response: {result['response'][:100]}...")
            results.append({"test": test_name, "status": "✅", "duration": duration})
        else:
            logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s)")
            logger.error(f"Error: {result['error']}")
            results.append({"test": test_name, "status": "❌", "duration": duration})

        time.sleep(1)

    # Résumé
    logger.info(f"\n{'='*60}")
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info(f"{'='*60}")

    for r in results:
        logger.info(f"{r['status']} {r['test']} - {r['duration']:.2f}s")

    success_count = sum(1 for r in results if r['status'] == "✅")
    logger.info(f"\nTotal: {success_count}/{len(results)} réussis")

    almaa.shutdown()

if __name__ == "__main__":
    test_complete()
