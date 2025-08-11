import sys
import click
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional

from core.base import Message
from core.communication import MessageBus
from core.memory.vector_store import VectorMemory
from core.debate_manager import DebateManager

from agents.enhanced_chef import EnhancedAgentChef
from agents.chef_projet import AgentChefProjet
from agents.memory_enhanced_worker import MemoryEnhancedWorker
from agents.special.philosophe import AgentPhilosophe

from utils.config import Config
from loguru import logger
from core.user_listener import UserListener

class ALMAA:
    """ALMAA v2.0 Phase 2 avec Débats et Mémoire - VERSION FINALE CORRIGÉE"""

    def __init__(self, config_path: str = "config/default_phase2.yaml"):
        logger.info("Initializing ALMAA v2.0 Phase 2...")

        # Configuration
        self.config = Config(config_path)

        # Message Bus
        self.bus = MessageBus()
        self.bus.start()
        logger.info("Message bus started")

        # Mémoire vectorielle
        self.memory = VectorMemory()

        # Debate Manager
        self.debate_manager = DebateManager(self.bus)
        logger.info("🎭 DebateManager initialized with moderator")

        # Agents
        self.agents = {}

        # Setup
        self._setup_core_agents()
        self._verify_agent_capabilities()
        self._setup_subscriptions()
        self._setup_debate_hooks()

        # ⚡ CORRECTION CRITIQUE: Boucle de traitement des débats
        self.processing_active = True
        self.processing_thread = None
        self._start_debate_processing()

        logger.success("ALMAA Phase 2 initialized with Debates and Memory!")

    def _setup_core_agents(self):
        """Configure les agents principaux avec capacités étendues"""

        # Enhanced Chef avec débat
        chef = EnhancedAgentChef()
        chef.debate_manager = self.debate_manager  # ⚡ LIEN CRITIQUE
        self.register_agent(chef)

        # Chef de Projet avec débat
        chef_projet = AgentChefProjet()
        self.register_agent(chef_projet)

        # Workers avec mémoire et débat
        specialties = ["coding", "analysis", "research"]
        for i, specialty in enumerate(specialties, 1):
            worker = MemoryEnhancedWorker(f"Worker{i}", specialty, self.memory)
            self.register_agent(worker)

        # Philosophe observateur
        philosophe = AgentPhilosophe()
        self.register_agent(philosophe)

        # User listener
        user_listener = UserListener()
        self.register_agent(user_listener)

        logger.info(f"Registered {len(self.agents)} enhanced agents")

    def _verify_agent_capabilities(self):
        """Vérifie les capacités des agents"""

        logger.info("🔍 Verifying agent capabilities...")

        debate_agents = []
        memory_agents = []

        for name, agent in self.agents.items():
            has_debate = hasattr(agent, 'participate_in_debate') or hasattr(agent, 'handle_debate_invitation')
            has_memory = hasattr(agent, 'memory') and hasattr(agent, 'remember_experience')

            logger.info(f"  • {name} ({getattr(agent, 'role', 'Unknown')}): debate={has_debate}, memory={has_memory}")

            if has_debate:
                debate_agents.append(name)
            if has_memory:
                memory_agents.append(name)

        logger.info(f"📊 Agents with debate capability: {debate_agents}")
        logger.info(f"🧠 Agents with memory capability: {memory_agents}")

        if len(debate_agents) >= 3:
            logger.success(f"✅ Sufficient debate participants available: {len(debate_agents)}")
        else:
            logger.warning(f"⚠️ Limited debate participants: {len(debate_agents)}")

        if len(memory_agents) > 0:
            logger.success(f"🧠 Memory features available for {len(memory_agents)} agents")
        else:
            logger.warning("⚠️ No memory-capable agents available")

    def _setup_subscriptions(self):
        """Configure les abonnements aux messages"""

        # Chef s'abonne aux réponses
        self.bus.subscribe("Chef", "TASK_RESULT")
        self.bus.subscribe("Chef", "DEBATE_RESULT")
        self.bus.subscribe("Chef", "ERROR")

        # ChefProjet s'abonne aux assignations
        self.bus.subscribe("ChefProjet", "TASK_ASSIGNMENT")

        # Workers s'abonnent aux tâches et débats
        for name, agent in self.agents.items():
            if "Worker" in name:
                self.bus.subscribe(name, "TASK_ASSIGNMENT")
                self.bus.subscribe(name, "CODE_TASK")
                self.bus.subscribe(name, "DEBATE_INVITATION")
                self.bus.subscribe(name, "REQUEST_ARGUMENT")

        # Philosophe observe tout
        self.bus.subscribe("Philosophe", "BROADCAST")

        logger.info("Message subscriptions configured")

    def _setup_debate_hooks(self):
        """Configure les hooks pour les débats"""

        # Handler pour les conclusions de débat
        def handle_debate_conclusion(message):
            try:
                if message.type == "DEBATE_CONCLUSION":
                    self.debate_manager.handle_debate_conclusion(message)
            except Exception as e:
                logger.error(f"Error in debate conclusion handler: {e}")

        self.bus.add_handler("DEBATE_CONCLUSION", handle_debate_conclusion)

        logger.info("Debate hooks configured")

    def _start_debate_processing(self):
        """Démarre la boucle de traitement des débats - NOUVELLE FONCTION CRITIQUE"""

        def processing_loop():
            """Boucle de traitement en arrière-plan"""

            logger.info("🔄 Starting debate processing loop")

            while self.processing_active:
                try:
                    # Traiter les messages des agents
                    self.bus.process_agent_messages()

                    # Traiter les débats actifs
                    for debate_id in list(self.debate_manager.active_debates.keys()):
                        self.debate_manager.process_debate_round(debate_id)

                    # Pause courte pour éviter la surcharge CPU
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    time.sleep(1)  # Pause plus longue en cas d'erreur

            logger.info("🛑 Debate processing loop stopped")

        # Lancer le thread de traitement
        self.processing_thread = threading.Thread(target=processing_loop, daemon=True)
        self.processing_thread.start()

        logger.info("🚀 Debate processing thread started")

    def register_agent(self, agent):
        """Enregistre un agent dans le système"""
        self.agents[agent.name] = agent
        self.bus.register_agent(agent)

    def process_request(self, request: str, timeout: int = 30) -> Dict[str, Any]:
        """Traite une requête utilisateur avec support débat"""

        start_time = time.time()

        # Créer le message initial
        message = Message(
            sender="User",
            recipient="Chef",
            type="REQUEST",
            content={"request": request}
        )

        # Publier sur le bus
        self.bus.publish(message)

        # Variables pour suivre la réponse
        response = None
        final_response = None
        debate_initiated = False

        # Attendre la réponse
        while (time.time() - start_time) < timeout:
            # Les messages sont traités automatiquement par le thread de traitement

            # Chercher une réponse pour l'utilisateur
            for agent in self.agents.values():
                messages_to_remove = []
                for msg in agent.outbox[:]:  # Copie pour modification sûre
                    if msg.recipient == "User" and msg.type == "RESPONSE":
                        if msg.content.get("status") == "debate_initiated":
                            response = msg
                            debate_initiated = True
                            logger.info(f"📨 Debate initiated response received")
                        elif msg.content.get("status") == "debate_completed":
                            final_response = msg
                            logger.info(f"📨 Debate completion response received")
                        else:
                            final_response = msg
                            logger.info(f"📨 Direct response received")

                        messages_to_remove.append(msg)

                # Retirer les messages traités
                for msg in messages_to_remove:
                    if msg in agent.outbox:
                        agent.outbox.remove(msg)

            # Si débat terminé ou réponse directe
            if final_response:
                break

            # Si débat initié mais pas encore terminé
            if debate_initiated and not final_response:
                # Continuer à attendre
                pass

            time.sleep(0.1)

        # Préparer la réponse
        end_time = time.time()
        duration = end_time - start_time

        if final_response:
            return {
                "success": True,
                "response": final_response.content.get("message", "Réponse reçue"),
                "details": final_response.content,
                "time": duration,
                "messages": self.bus.get_stats()["messages_sent"],
                "debate_used": debate_initiated
            }
        elif response:
            return {
                "success": True, 
                "response": response.content.get("message", "Débat en cours..."),
                "details": response.content,
                "time": duration,
                "messages": self.bus.get_stats()["messages_sent"],
                "debate_used": True,
                "status": "debate_in_progress"
            }
        else:
            return {
                "success": False,
                "error": "Timeout - aucune réponse reçue",
                "time": duration,
                "messages": self.bus.get_stats()["messages_sent"],
                "debate_used": debate_initiated
            }

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du système"""

        agent_status = {}
        for name, agent in self.agents.items():
            has_debate = hasattr(agent, 'participate_in_debate')
            has_memory = hasattr(agent, 'memory')

            capabilities = []
            if has_debate:
                capabilities.append("💬")
            if has_memory:
                capabilities.append("🧠")

            agent_status[name] = {
                "role": getattr(agent, 'role', 'Unknown'),
                "state": getattr(agent, 'state', 'unknown'),
                "capabilities": "".join(capabilities)
            }

        return {
            "agents": agent_status,
            "bus": self.bus.get_stats(),
            "debates": {
                "active": len(self.debate_manager.active_debates),
                "total_results": len(getattr(self.debate_manager, 'debate_results', {}))
            },
            "memory": {
                "stats": self.memory.get_stats() if hasattr(self.memory, 'get_stats') else {}
            }
        }

    def get_debate_status(self) -> Dict[str, Any]:
        """Retourne le statut des débats"""

        active_debates = {}
        for debate_id, info in self.debate_manager.active_debates.items():
            # Obtenir statut du moderator
            mod_status = self.debate_manager.moderator.get_debate_status(debate_id)

            active_debates[debate_id] = {
                "topic": info.get("topic", "Unknown"),
                "status": mod_status.get("status", "unknown") if mod_status else "unknown",
                "participants": info.get("participants", []),
                "duration": str(time.time() - info.get("start_time", time.time()))
            }

        return {
            "active_count": len(active_debates),
            "debates": active_debates
        }

    def shutdown(self):
        """Arrêt propre du système"""

        logger.info("Shutting down ALMAA Phase 2...")

        # Arrêter le traitement
        self.processing_active = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)

        # Arrêter le bus
        self.bus.stop()

        logger.success("ALMAA Phase 2 shutdown complete")

# CLI avec toutes les fonctions
@click.group()
@click.pass_context
def cli(ctx):
    """ALMAA v2.0 Phase 2 - Système Multi-Agents avec Débats et Mémoire"""
    ctx.ensure_object(dict)

@cli.command()
@click.pass_context
def interactive(ctx):
    """Lance le mode interactif avec support complet des débats"""

    almaa = ALMAA()

    click.echo("🤖 ALMAA v2.0 Phase 2 - Interactive Mode")
    click.echo("Features: Debates 💬 | Memory 🧠 | Learning 📚")
    click.echo("Type 'exit' to quit, '/help' for help")
    click.echo("-" * 50)

    while True:
        try:
            user_input = click.prompt("Vous", type=str)

            if user_input.lower() == 'exit':
                break
            elif user_input == '/help':
                show_help()
                continue
            elif user_input == '/status':
                show_status(almaa)
                continue
            elif user_input == '/memory':
                show_memory_stats(almaa)
                continue
            elif user_input == '/debates':
                show_debate_status(almaa)
                continue

            # Traiter la requête
            click.echo("🔄 Processing...")
            result = almaa.process_request(user_input, timeout=60)  # Plus de temps pour débats

            # Afficher résultat
            if result['success']:
                click.echo(f"✅ ALMAA: {result['response']}")
                if result.get('debate_used'):
                    click.echo("🎭 Cette réponse impliquait un débat entre experts")
                click.echo(f"⏱️  Time: {result['time']:.2f}s | Messages: {result['messages']}")
            else:
                click.echo(f"❌ Erreur: {result['error']}")
                click.echo(f"⏱️  Time: {result['time']:.2f}s")

            click.echo("-" * 50)

        except KeyboardInterrupt:
            click.echo("\n")
            continue
        except Exception as e:
            click.echo(f"\n❌ Erreur système: {str(e)}")

    almaa.shutdown()
    click.echo("\n👋 ALMAA Phase 2 session ended!")

def show_help():
    """Affiche l'aide complète"""
    help_text = """
🤖 ALMAA Phase 2 Commands:
  /help     - Show this help
  /status   - System status
  /memory   - Memory statistics
  /debates  - Active debates
  exit      - Quit

💡 Example queries:
  - "What's the best architecture for a payment system?"
  - "Create a Python function for calculating Fibonacci"
  - "Analyze this code and suggest improvements"
    """
    click.echo(help_text)

def show_memory_stats(almaa):
    """Affiche les statistiques mémoire"""
    stats = almaa.memory.get_stats() if hasattr(almaa.memory, 'get_stats') else {}

    click.echo("\n🧠 Memory Statistics:")
    if stats:
        for key, value in stats.items():
            click.echo(f"  • {key}: {value}")
    else:
        click.echo("  • No memory statistics available")

def show_debate_status(almaa):
    """Affiche le statut des débats"""
    debate_status = almaa.get_debate_status()

    click.echo("\n💬 Debate Status:")
    click.echo(f"  • Active debates: {debate_status['active_count']}")

    for debate_id, info in debate_status['debates'].items():
        short_id = debate_id[:8]
        click.echo(f"    - {short_id}: {info['status']}")

def show_status(almaa):
    """Affiche le statut complet"""
    status = almaa.get_status()

    click.echo("\n📊 ALMAA Phase 2 Status")
    click.echo("=" * 50)

    # Agents
    agent_count = len(status['agents'])
    debate_capable = len([a for a in status['agents'].values() if '💬' in a.get('capabilities', '')])
    memory_capable = len([a for a in status['agents'].values() if '🧠' in a.get('capabilities', '')])

    click.echo(f"\n🤖 Agents ({agent_count} total):")
    click.echo(f"  • With debate capability: {debate_capable}")
    click.echo(f"  • With memory capability: {memory_capable}")

    for name, info in status['agents'].items():
        click.echo(f"    - {name} ({info['role']}): {info['state']} {info['capabilities']}")

    # Bus
    bus_stats = status['bus']
    click.echo(f"\n📨 Message Bus:")
    click.echo(f"  • Messages sent: {bus_stats['messages_sent']}")
    click.echo(f"  • Messages delivered: {bus_stats['messages_delivered']}")

    # Debates
    debate_stats = status['debates']
    click.echo(f"\n💬 Debates:")
    click.echo(f"  • Active: {debate_stats['active']}")

    click.echo("=" * 50)

if __name__ == '__main__':
    cli(obj={})
