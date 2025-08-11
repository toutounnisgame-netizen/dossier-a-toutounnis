# -*- coding: utf-8 -*-
"""
ALMAA v2.0 Debug FIXED - Avec MessageBus Synchrone
Résout le problème de timeout définitivement
"""
import sys
import click
import time
from pathlib import Path
from typing import Dict, Any, Optional

from core.base import Message
from core.messagebus_sync import MessageBusSync  # Import du bus synchrone
from core.memory.vector_store import VectorMemory
from agents.simple_chef import SimpleChef
from agents.special.philosophe import AgentPhilosophe
from utils.config import Config
from loguru import logger
from core.user_listener import UserListener


class ALMAAFixed:
    """ALMAA Debug Mode FIXED - Avec MessageBus fonctionnel"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = Config(config_path or "config/default_phase2.yaml")
        self.bus = MessageBusSync()  # Utiliser le bus synchrone
        self.memory = VectorMemory()
        self.agents = {}
        
        logger.info("Initializing ALMAA Debug FIXED...")
        
        self._setup_simple_agents()
        self._setup_subscriptions()
        
        logger.success("ALMAA Debug FIXED initialized!")
        
    def _setup_simple_agents(self):
        """Setup minimal agents for debugging"""
        # Simple Chef
        chef = SimpleChef()
        self.register_agent(chef)
        
        # User Listener
        user_listener = UserListener()
        self.register_agent(user_listener)
        
        # Philosophe for observation
        philosophe = AgentPhilosophe()
        self.register_agent(philosophe)
        
        logger.info(f"Registered {len(self.agents)} simple agents")
        
    def _setup_subscriptions(self):
        """Setup message subscriptions"""
        # Chef s'abonne aux REQUEST
        self.bus.subscribe("Chef", "REQUEST")
        # User s'abonne aux RESPONSE
        self.bus.subscribe("User", "RESPONSE")
        
    def register_agent(self, agent):
        """Register an agent with the system"""
        self.agents[agent.name] = agent
        agent.bus = self.bus
        self.bus.register_agent(agent)
        
    def process_request(self, request: str, timeout: int = 30) -> Dict[str, Any]:
        """Process a user request with FIXED message handling"""
        logger.info(f"FIXED processing request: {request}")
        
        # Create user message
        message = Message(
            sender="User",
            recipient="",  # Broadcast aux abonnés REQUEST
            type="REQUEST",
            content={"request": request}
        )
        
        start_time = time.time()
        
        try:
            # Publier le message (traitement synchrone)
            self.bus.publish(message)
            
            # Chercher la réponse
            user_agent = self.agents.get("User")
            if user_agent and user_agent.inbox:
                # Traiter les messages de User
                while user_agent.inbox:
                    response_msg = user_agent.inbox.pop(0)
                    if response_msg.type == "RESPONSE":
                        processing_time = time.time() - start_time
                        logger.info(f"Response received in {processing_time:.2f}s!")
                        
                        return {
                            "status": "success",
                            "response": response_msg.content.get("message", "No message"),
                            "time": processing_time,
                            "details": response_msg.content
                        }
            
            # Si pas de réponse immédiate, c'est un problème
            processing_time = time.time() - start_time
            return {
                "status": "no_response",
                "response": "No response generated",
                "time": processing_time,
                "debug_info": self.get_debug_info()
            }
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {
                "status": "error",
                "response": f"Processing error: {str(e)}",
                "time": time.time() - start_time,
                "debug_info": self.get_debug_info()
            }
        
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information"""
        info = {
            "agents": list(self.agents.keys()),
            "bus_stats": self.bus.get_stats(),
            "memory_ready": self.memory.is_ready() if self.memory else False
        }
        
        # Add agent-specific info
        for name, agent in self.agents.items():
            info[f"agent_{name}"] = {
                "inbox_size": len(getattr(agent, 'inbox', [])),
                "processed_messages": getattr(agent, 'processed_messages', set())
            }
            
        return info
        
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "mode": "debug_fixed",
            "agents": len(self.agents),
            "bus_active": self.bus is not None,
            "memory_ready": self.memory.is_ready() if self.memory else False
        }
        
    def shutdown(self):
        """Shutdown the system"""
        logger.info("Shutting down ALMAA Debug FIXED...")
        if self.bus:
            self.bus.stop()
        logger.success("ALMAA Debug FIXED shutdown complete")


@click.group()
@click.pass_context
def cli(ctx):
    """ALMAA Debug FIXED CLI"""
    ctx.ensure_object(dict)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Launch interactive debug FIXED mode"""
    try:
        # Initialize FIXED version
        almaa = ALMAAFixed()
        ctx.obj['almaa'] = almaa
        
        print("🔧 ALMAA v2.0 Debug FIXED")
        print("Features: MessageBus Synchrone ✅ | Délivrance Garantie 📬 | Logs Détaillés 📝")
        print("Type 'exit' to quit, '/help' for help")
        print("--" * 30)
        
        while True:
            try:
                user_input = input("Fixed> ").strip()
                
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == '/help':
                    show_help()
                elif user_input.lower() == '/status':
                    show_status(almaa)
                elif user_input.lower() == '/info':
                    show_debug_info(almaa)
                elif user_input:
                    print("🔄 Processing (FIXED Mode)...")
                    result = almaa.process_request(user_input)
                    
                    if result["status"] == "success":
                        print(f"✅ ALMAA: {result['response']}")
                        print(f"⏱️  Time: {result['time']:.2f}s")
                    else:
                        print(f"❌ {result['status'].upper()}: {result['response']}")
                        if "debug_info" in result:
                            print(f"🐛 Debug: {result['debug_info']}")
                    
                    # Afficher stats
                    stats = almaa.bus.get_stats()
                    print(f"📊 Messages: sent={stats['messages_sent']}, delivered={stats['messages_delivered']}")
                    print("--" * 30)
                    
            except (KeyboardInterrupt, EOFError):
                break
        
        almaa.shutdown()
        print("👋 Debug FIXED session ended!")
        
    except Exception as e:
        logger.error(f"Debug FIXED mode error: {e}")
        print(f"❌ Error: {e}")


def show_help():
    """Show debug commands"""
    print("\n🔧 Debug FIXED Commands:")
    print("/help    - Show this help")
    print("/status  - Show system status")
    print("/info    - Show detailed debug info")
    print("exit     - Exit debug mode")
    print()


def show_status(almaa):
    """Show debug status"""
    status = almaa.get_status()
    print("\n📊 Debug FIXED Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()


def show_debug_info(almaa):
    """Show detailed debug info"""
    info = almaa.get_debug_info()
    print("\n🔍 Debug FIXED Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()


if __name__ == "__main__":
    cli(obj={})