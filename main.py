#!/usr/bin/env python3
"""
ALMAA v2.0 - Autonomous Local Multi-Agent Architecture
Point d'entrée principal du système
"""

import sys
import click
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Imports ALMAA
from core.base import Message
from core.communication import MessageBus
from agents.chef import AgentChef
from agents.chef_projet import AgentChefProjet
from agents.workers.developer import DeveloperAgent
from utils.config import Config
from loguru import logger
from core.user_listener import UserListener
from agents.special.philosophe import AgentPhilosophe

# Configuration du logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO"
)

class ALMAA:
    """Classe principale du système ALMAA"""

    def __init__(self, config_path: str = "config/default.yaml"):
        logger.info("Initializing ALMAA system...")

        # Configuration
        self.config = Config(config_path)

        # Message Bus
        self.bus = MessageBus()
        self.bus.start()

        # Agents
        self.agents = {}

        # Setup
        self._setup_core_agents()
        self._setup_subscriptions()

        # Hook pour que le Philosophe observe tous les messages
        original_publish = self.bus.publish

        def publish_with_observation(message):
            # Publication normale
            result = original_publish(message)
        
            # Le Philosophe observe
            if "Philosophe" in self.agents:
                self.agents["Philosophe"].observe_message(message)
        
            return result
    
        self.bus.publish = publish_with_observation

        logger.success("ALMAA system initialized!")

    def _setup_core_agents(self):
        """Configure les agents principaux"""

        # Agent Chef (CEO)
        chef = AgentChef()
        self.register_agent(chef)

        # Chef de Projet
        chef_projet = AgentChefProjet()
        self.register_agent(chef_projet)

        # Développeur fonctionnel
        dev = DeveloperAgent("Developer1")
        self.register_agent(dev)

        # Agent Philosophe
        philosophe = AgentPhilosophe()
        self.register_agent(philosophe)

        # User listener
        user_listener = UserListener()
        self.register_agent(user_listener)

        logger.info(f"Registered {len(self.agents)} core agents")

    def _setup_subscriptions(self):
        """Configure les abonnements aux messages"""

        # Chef de Projet s'abonne aux assignations
        self.bus.subscribe("ChefProjet", "TASK_ASSIGNMENT")

        # Développeurs s'abonnent aux tâches de code
        for name, agent in self.agents.items():
            if "Developer" in name:
                self.bus.subscribe(name, "CODE_TASK")
                self.bus.subscribe(name, "TASK_ASSIGNMENT")

        # Chef s'abonne aux résultats
        self.bus.subscribe("Chef", "TASK_RESULT")
        self.bus.subscribe("Chef", "ERROR")

    def register_agent(self, agent):
        """Enregistre un agent dans le système"""

        self.agents[agent.name] = agent
        self.bus.register_agent(agent)

    def process_request(self, request: str, timeout: int = 30) -> Dict[str, Any]:
        """Traite une requête utilisateur"""

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

        # Attendre la réponse
        response = None
        while (time.time() - start_time) < timeout:
            # Traiter les messages des agents
            self.bus.process_agent_messages()

            # Chercher une réponse pour l'utilisateur
            # CORRECTION: On cherche dans l'agent "User" directement
            if "User" in self.agents:
                user_agent = self.agents["User"]
                for msg in list(user_agent.inbox):  # list() pour éviter modification pendant itération
                    if msg.type == "RESPONSE":
                        response = msg
                        user_agent.inbox.remove(msg)
                        break

            if response:
                break

            time.sleep(0.1)

        # Calculer les statistiques
        end_time = time.time()
        stats = {
            "duration": end_time - start_time,
            "messages": self.bus.stats["messages_sent"],
            "agents_used": len([a for a in self.agents.values() if a.state != "idle"])
        }

        if response:
            return {
                "success": True,
                "response": response.content.get("message", response.content),
                "stats": stats
            }
        else:
            return {
                "success": False,
                "error": "Timeout - no response received",
                "stats": stats
            }

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du système"""

        return {
            "agents": {
                name: agent.get_state() 
                for name, agent in self.agents.items()
            },
            "bus": self.bus.get_stats(),
            "config": {
                "version": self.config.get("system.version"),
                "debug": self.config.get("system.debug")
            }
        }

    def shutdown(self):
        """Arrêt propre du système"""

        logger.info("Shutting down ALMAA...")
        self.bus.stop()
        logger.success("ALMAA shutdown complete")


# CLI Commands
@click.group()
@click.pass_context
def cli(ctx):
    """ALMAA - Système Multi-Agents Autonome"""
    ctx.ensure_object(dict)
    ctx.obj['almaa'] = ALMAA()

@cli.command()
@click.pass_context
def interactive(ctx):
    """Lance le mode interactif"""

    almaa = ctx.obj['almaa']

    click.echo("🤖 ALMAA v2.0 - Mode Interactif")
    click.echo("Tapez 'exit' pour quitter, '/help' pour l'aide")
    click.echo("-" * 50)

    while True:
        try:
            # Prompt utilisateur
            user_input = click.prompt("Vous", type=str)

            # Commandes spéciales
            if user_input.lower() == 'exit':
                break
            elif user_input == '/help':
                show_help()
                continue
            elif user_input == '/status':
                show_status(almaa)
                continue
            elif user_input == '/agents':
                show_agents(almaa)
                continue

            # Traiter la requête
            click.echo("🔄 Traitement en cours...")
            result = almaa.process_request(user_input)

            # Afficher la réponse
            if result['success']:
                click.echo(f"🤖 ALMAA: {result['response']}")
                click.echo(f"⏱️  Temps: {result['stats']['duration']:.2f}s")
            else:
                click.echo(f"❌ Erreur: {result['error']}")

            click.echo("-" * 50)

        except KeyboardInterrupt:
            click.echo("")
            continue
        except Exception as e:
            click.echo(f"❌ Erreur système: {str(e)}")

    # Shutdown
    almaa.shutdown()
    click.echo("👋 Au revoir!")

@cli.command()
@click.argument('request')
@click.pass_context
def process(ctx, request):
    """Traite une requête unique"""

    almaa = ctx.obj['almaa']

    click.echo(f"🔄 Traitement: {request}")
    result = almaa.process_request(request)

    if result['success']:
        click.echo(f"✅ Réponse: {result['response']}")
    else:
        click.echo(f"❌ Erreur: {result['error']}")

    click.echo(f"⏱️  Temps: {result['stats']['duration']:.2f}s")

    almaa.shutdown()

@cli.command()
@click.pass_context
def status(ctx):
    """Affiche le statut du système"""

    almaa = ctx.obj['almaa']
    show_status(almaa)
    almaa.shutdown()

# Fonctions d'aide
def show_help():
    """Affiche l'aide"""

    help_text = """
Commandes disponibles:
  /help     - Affiche cette aide
  /status   - Affiche le statut du système
  /agents   - Liste les agents actifs
  /clear    - Efface l'écran
  exit      - Quitte le programme

Exemples de requêtes:
  - "Crée une fonction Python pour calculer fibonacci"
  - "Analyse ce code et propose des améliorations"
  - "Écris un script bash pour sauvegarder des fichiers"
    """
    click.echo(help_text)

def show_status(almaa):
    """Affiche le statut détaillé"""

    status = almaa.get_status()

    click.echo("📊 Statut du Système ALMAA")
    click.echo("=" * 50)

    # Agents
    click.echo(f"🤖 Agents ({len(status['agents'])} actifs):")
    for name, state in status['agents'].items():
        click.echo(f"  - {name}: {state['state']} (inbox: {state['inbox_count']})")

    # Bus
    bus_stats = status['bus']
    click.echo(f"📨 Message Bus:")
    click.echo(f"  - Messages envoyés: {bus_stats['messages_sent']}")
    click.echo(f"  - Messages délivrés: {bus_stats['messages_delivered']}")
    click.echo(f"  - Échecs: {bus_stats['messages_failed']}")

    # Configuration
    click.echo(f"⚙️  Configuration:")
    click.echo(f"  - Version: {status['config']['version']}")
    click.echo(f"  - Debug: {status['config']['debug']}")

    click.echo("=" * 50)

def show_agents(almaa):
    """Affiche la liste des agents"""

    click.echo("🤖 Agents Actifs:")
    click.echo("-" * 40)

    for name, agent in almaa.agents.items():
        state = agent.get_state()
        click.echo(f"{name} ({agent.role}):")
        click.echo(f"  État: {state['state']}")
        click.echo(f"  Messages en attente: {state['inbox_count']}")
        click.echo(f"  Créé: {state['created_at']}")

# Point d'entrée
if __name__ == '__main__':
    cli(obj={})
