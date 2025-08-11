# -*- coding: utf-8 -*-
"""
ALMAA v2.0 SOLUTION COMPLÈTE - Main Fixed
Système ALMAA avec gestion robuste des réponses
Résout définitivement le problème de perte de messages
"""
import sys
import click
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Imports ALMAA
from core.base import Message
from core.enhanced_messagebus import EnhancedMessageBus
from core.response_manager import ResponseManager
from core.memory.vector_store import VectorMemory
from agents.simple_chef import SimpleChef
from agents.user_response_collector import UserResponseCollector
from agents.special.philosophe import AgentPhilosophe
from utils.config import Config
from loguru import logger

# Configuration logging optimisée
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO"
)


class ALMAAComplete:
    """Système ALMAA complet avec gestion robuste des réponses"""
    
    def __init__(self, config_path: Optional[str] = None):
        logger.info("🚀 Initializing ALMAA Complete System...")
        
        # Configuration
        self.config = Config(config_path or "config/default_phase2.yaml")
        
        # Composants centraux
        self.response_manager = ResponseManager()
        self.bus = EnhancedMessageBus(self.response_manager)
        self.memory = VectorMemory()
        self.agents = {}
        
        # Setup
        self._setup_core_agents()
        self._setup_subscriptions()
        self._start_system()
        
        logger.success("✅ ALMAA Complete System initialized!")
        
    def _setup_core_agents(self):
        """Configure les agents principaux avec gestion robuste"""
        
        # Agent Chef (simplifié mais efficace)
        chef = SimpleChef()
        self.register_agent(chef)
        
        # Collector de réponses (remplace UserListener)
        user_collector = UserResponseCollector(self.response_manager)
        self.register_agent(user_collector)
        
        # Philosophe observateur
        philosophe = AgentPhilosophe()
        self.register_agent(philosophe)
        
        logger.info(f"✅ Registered {len(self.agents)} core agents")
        
    def _setup_subscriptions(self):
        """Configure les abonnements aux messages"""
        
        # Chef s'abonne aux REQUEST
        self.bus.subscribe("Chef", "REQUEST")
        
        # User collector s'abonne aux RESPONSE
        self.bus.subscribe("User", "RESPONSE")
        self.bus.subscribe("User", "ERROR")
        self.bus.subscribe("User", "TASK_RESULT")
        
        logger.debug("✅ Message subscriptions configured")
        
    def _start_system(self):
        """Démarre le système complet"""
        self.bus.start()
        logger.info("✅ Enhanced MessageBus started")
        
    def register_agent(self, agent):
        """Enregistre un agent dans le système"""
        self.agents[agent.name] = agent
        self.bus.register_agent(agent)
        
    def process_request(self, request: str, timeout: int = 30) -> Dict[str, Any]:
        """Traite une requête utilisateur avec gestion robuste"""
        
        start_time = time.time()
        logger.info(f"🔄 Processing request: {request[:50]}...")
        
        try:
            # Créer une requête trackée
            request_id = self.response_manager.create_request(request, timeout)
            
            # Créer le message initial avec metadata
            message = Message(
                sender="User",
                recipient="",  # Sera routé automatiquement vers Chef
                type="REQUEST",
                content={"request": request, "request_id": request_id},
                thread_id=request_id
            )
            
            # Publier sur le bus amélioré
            self.bus.publish(message)
            
            # Traiter les messages des agents
            max_iterations = timeout * 10  # 10 iterations par seconde
            for i in range(max_iterations):
                self.bus.process_agent_messages()
                
                # Vérifier si une réponse est disponible
                result = self.response_manager.get_response(request_id, wait_timeout=0.1)
                
                if result["success"]:
                    processing_time = time.time() - start_time
                    logger.success(f"✅ Request completed in {processing_time:.2f}s")
                    
                    return {
                        "success": True,
                        "response": result["response"],
                        "processing_time": processing_time,
                        "stats": self._get_processing_stats(),
                        "request_id": request_id
                    }
                elif "error" in result and result["error"] in ["Request timeout", "Response retrieval timeout"]:
                    # Continue si c'est juste un timeout de récupération
                    continue
                else:
                    # Erreur définitive
                    processing_time = time.time() - start_time
                    logger.error(f"❌ Request failed: {result.get('error', 'Unknown error')}")
                    
                    return {
                        "success": False,
                        "error": result.get("error", "Processing failed"),
                        "processing_time": processing_time,
                        "stats": self._get_processing_stats(),
                        "request_id": request_id
                    }
                
                time.sleep(0.1)
            
            # Timeout global
            processing_time = time.time() - start_time
            logger.error(f"⏱️ Request timeout after {processing_time:.2f}s")
            
            return {
                "success": False,
                "error": "Global timeout - no response received",
                "processing_time": processing_time,
                "stats": self._get_processing_stats(),
                "request_id": request_id
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"💥 Processing exception: {e}")
            
            return {
                "success": False,
                "error": f"System error: {str(e)}",
                "processing_time": processing_time,
                "stats": self._get_processing_stats()
            }
            
    def _get_processing_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de traitement"""
        return {
            "bus_stats": self.bus.get_stats(),
            "response_manager": self.response_manager.get_stats(),
            "agents_count": len(self.agents),
            "memory_ready": self.memory.is_ready() if self.memory else False
        }
        
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut complet du système"""
        return {
            "system": {
                "name": "ALMAA Complete",
                "version": "2.0",
                "status": "running",
                "uptime": "N/A"  # À implémenter
            },
            "agents": {
                name: {
                    "role": agent.role,
                    "state": agent.state,
                    "inbox_count": len(agent.inbox) if hasattr(agent, 'inbox') else 0
                }
                for name, agent in self.agents.items()
            },
            "components": {
                "message_bus": self.bus.get_stats(),
                "response_manager": self.response_manager.get_stats(),
                "memory": self.memory.get_stats() if self.memory else {"status": "disabled"}
            }
        }
        
    def shutdown(self):
        """Arrêt propre du système"""
        logger.info("🛑 Shutting down ALMAA Complete...")
        
        self.bus.stop()
        self.response_manager.shutdown()
        
        logger.success("✅ ALMAA Complete shutdown complete")


# CLI Commands
@click.group()
@click.pass_context
def cli(ctx):
    """ALMAA Complete - Système Multi-Agents Robuste"""
    ctx.ensure_object(dict)


@cli.command()
@click.option('--config', default=None, help='Fichier de configuration')
@click.pass_context
def interactive(ctx, config):
    """Lance le mode interactif robuste"""
    
    try:
        almaa = ALMAAComplete(config)
        ctx.obj['almaa'] = almaa
        
        print("🤖 ALMAA v2.0 COMPLETE - Mode Interactif")
        print("Features: Gestion Robuste des Réponses ✅ | MessageBus Amélioré 🚀 | Zero Perte 📬")
        print("Type 'exit' to quit, '/help' for help")
        print("─" * 80)
        
        request_count = 0
        
        while True:
            try:
                user_input = input(f"[{request_count}] Vous> ").strip()
                
                if user_input.lower() == 'exit':
                    break
                elif user_input == '/help':
                    show_help()
                    continue
                elif user_input == '/status':
                    show_status(almaa)
                    continue
                elif user_input == '/stats':
                    show_detailed_stats(almaa)
                    continue
                elif user_input == '/clear':
                    clear_screen()
                    continue
                elif user_input:
                    print("🔄 Processing...")
                    
                    result = almaa.process_request(user_input)
                    request_count += 1
                    
                    if result["success"]:
                        print(f"✅ ALMAA: {result['response']}")
                        print(f"⏱️  Time: {result['processing_time']:.2f}s | "
                              f"Messages: {result['stats']['bus_stats']['messages_sent']}")
                    else:
                        print(f"❌ ERROR: {result['error']}")
                        if "stats" in result:
                            print(f"🐛 Debug: {result['stats']}")
                    
                    print("─" * 80)
                    
            except (KeyboardInterrupt, EOFError):
                print("\n")
                break
            except Exception as e:
                print(f"💥 Unexpected error: {e}")
                logger.error(f"Interactive mode error: {e}")
        
        almaa.shutdown()
        print("👋 ALMAA Complete session ended!")
        
    except Exception as e:
        logger.error(f"System initialization error: {e}")
        print(f"💥 Failed to start ALMAA: {e}")


@cli.command()
@click.argument('request')
@click.option('--timeout', default=30, help='Timeout en secondes')
@click.pass_context
def process(ctx, request, timeout):
    """Traite une requête unique"""
    
    try:
        almaa = ALMAAComplete()
        
        print(f"🔄 Processing: {request}")
        result = almaa.process_request(request, timeout)
        
        if result["success"]:
            print(f"✅ Response: {result['response']}")
        else:
            print(f"❌ Error: {result['error']}")
        
        print(f"⏱️  Time: {result['processing_time']:.2f}s")
        
        almaa.shutdown()
        
    except Exception as e:
        print(f"💥 Error: {e}")


# Fonctions d'aide
def show_help():
    """Affiche l'aide"""
    help_text = """
🤖 ALMAA Complete - Commandes Disponibles:

📋 Commandes Système:
  /help     - Affiche cette aide
  /status   - Affiche le statut du système  
  /stats    - Statistiques détaillées
  /clear    - Efface l'écran
  exit      - Quitte le programme

💬 Exemples de Requêtes:
  • "Bonjour, comment ça va ?"
  • "Explique-moi les algorithmes de tri"
  • "Créé une fonction Python pour calculer fibonacci"
  • "Analyse ce problème et propose une solution"

🔧 Fonctionnalités:
  ✅ Gestion robuste des réponses (zéro perte)
  ✅ MessageBus intelligent avec routing
  ✅ Système de retry automatique
  ✅ Monitoring en temps réel
    """
    print(help_text)


def show_status(almaa):
    """Affiche le statut du système"""
    status = almaa.get_status()
    
    print("\n📊 ALMAA Complete - System Status")
    print("=" * 60)
    
    # Système
    sys_info = status["system"]
    print(f"🤖 System: {sys_info['name']} v{sys_info['version']} ({sys_info['status']})")
    
    # Agents
    print(f"\n👥 Agents ({len(status['agents'])} active):")
    for name, info in status['agents'].items():
        print(f"  • {name}: {info['role']} [{info['state']}] (inbox: {info['inbox_count']})")
    
    # Composants
    components = status["components"]
    bus_stats = components["message_bus"]
    resp_stats = components["response_manager"]
    
    print(f"\n📨 Message Bus:")
    print(f"  • Sent: {bus_stats['messages_sent']} | Delivered: {bus_stats['messages_delivered']}")
    print(f"  • Failed: {bus_stats['messages_failed']} | Queue: {bus_stats['queue_size']}")
    
    print(f"\n🎯 Response Manager:")
    print(f"  • Requests: {resp_stats['requests_created']} | Responses: {resp_stats['responses_received']}")
    print(f"  • Pending: {resp_stats['pending_requests']} | Timeouts: {resp_stats['timeouts']}")
    
    print("=" * 60)


def show_detailed_stats(almaa):
    """Affiche les statistiques détaillées"""
    stats = almaa._get_processing_stats()
    
    print("\n📈 ALMAA Complete - Detailed Statistics")
    print("=" * 60)
    
    import json
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    print("=" * 60)


def clear_screen():
    """Efface l'écran"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == '__main__':
    cli(obj={})