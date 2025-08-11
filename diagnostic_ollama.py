#!/usr/bin/env python3
"""
Test et diagnostic Ollama pour ALMAA
"""

import subprocess
import time
import requests
import ollama
import os
from pathlib import Path


def check_ollama_process():
    """Vérifier si Ollama est en cours d'exécution"""
    try:
        result = subprocess.run(['tasklist'], capture_output=True, text=True, shell=True)
        if 'ollama.exe' in result.stdout:
            print("✅ Processus Ollama détecté")
            return True
        else:
            print("❌ Processus Ollama non trouvé")
            return False
    except Exception as e:
        print(f"❌ Erreur vérification processus: {e}")
        return False


def check_ollama_port():
    """Vérifier si Ollama écoute sur le port 11434"""
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True, shell=True)
        if ':11434' in result.stdout:
            print("✅ Port 11434 ouvert")
            return True
        else:
            print("❌ Port 11434 non trouvé")
            return False
    except Exception as e:
        print(f"❌ Erreur vérification port: {e}")
        return False


def test_ollama_api():
    """Tester l'API Ollama"""
    urls_to_try = [
        'http://localhost:11434/api/version',
        'http://127.0.0.1:11434/api/version',
        'http://0.0.0.0:11434/api/version'
    ]
    
    for url in urls_to_try:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ API Ollama accessible via {url}")
                print(f"   Version: {response.json()}")
                return True
        except Exception as e:
            print(f"❌ API {url} non accessible: {e}")
            
    return False


def test_ollama_python():
    """Tester Ollama via Python"""
    hosts_to_try = [
        'http://localhost:11434',
        'http://127.0.0.1:11434',
        'http://0.0.0.0:11434'
    ]
    
    for host in hosts_to_try:
        try:
            client = ollama.Client(host=host)
            response = client.generate(
                model='solar:10.7b',
                prompt='Test',
                options={'num_predict': 3}
            )
            print(f"✅ Ollama Python OK via {host}")
            print(f"   Response: {response['response']}")
            return True
        except Exception as e:
            print(f"❌ Ollama Python {host}: {e}")
            
    return False


def restart_ollama():
    """Redémarrer Ollama proprement"""
    print("🔄 Redémarrage d'Ollama...")
    
    # Arrêter tous les processus Ollama
    try:
        subprocess.run(['taskkill', '/f', '/im', 'ollama.exe'], 
                      capture_output=True, shell=True)
        print("   Arrêt des processus Ollama...")
        time.sleep(3)
    except:
        pass
    
    # Redémarrer Ollama en arrière-plan
    try:
        print("   Démarrage d'Ollama serve...")
        # Utiliser Popen pour démarrer en arrière-plan
        process = subprocess.Popen(
            ['ollama', 'serve'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)  # Attendre le démarrage
        
        # Vérifier si ça marche
        if test_ollama_api():
            print("✅ Ollama redémarré avec succès")
            return True
        else:
            print("❌ Échec du redémarrage")
            return False
            
    except Exception as e:
        print(f"❌ Erreur redémarrage: {e}")
        return False


def main():
    """Diagnostic complet d'Ollama"""
    print("🔍 DIAGNOSTIC OLLAMA POUR ALMAA")
    print("=" * 50)
    
    # Étape 1: Processus
    print("\n1. Vérification processus:")
    process_ok = check_ollama_process()
    
    # Étape 2: Port
    print("\n2. Vérification port:")
    port_ok = check_ollama_port()
    
    # Étape 3: API
    print("\n3. Test API:")
    api_ok = test_ollama_api()
    
    # Étape 4: Python
    print("\n4. Test Python:")
    python_ok = test_ollama_python()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ:")
    
    if all([process_ok, port_ok, api_ok, python_ok]):
        print("✅ Ollama fonctionne parfaitement!")
        print("   Le problème vient d'ailleurs dans ALMAA")
        return True
        
    elif process_ok and not (port_ok and api_ok):
        print("⚠️  Ollama lancé mais pas accessible")
        print("   Essai de redémarrage...")
        if restart_ollama():
            return True
        
    elif not process_ok:
        print("❌ Ollama non démarré")
        print("   Essai de démarrage...")
        if restart_ollama():
            return True
    
    # Solutions alternatives
    print("\n💡 SOLUTIONS ALTERNATIVES:")
    print("1. Démarrer manuellement: ollama serve")
    print("2. Vérifier l'installation: ollama --version")
    print("3. Réinstaller Ollama depuis https://ollama.ai")
    
    return False


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 OLLAMA OK - Vous pouvez lancer ALMAA:")
        print("   python main_phase2.py interactive")
    else:
        print("\n❌ OLLAMA KO - Corrigez les problèmes ci-dessus")
        
    input("\nAppuyez sur Entrée pour continuer...")