from typing import List, Dict, Optional, Any
from datetime import datetime
from core.communication import MessageBus
from core.base import Message
from core.debate import Debate
from core.voting import VotingSystem
from agents.special.moderator import DebateModerator
from loguru import logger

class DebateManager:
    """Gestionnaire de débats complet - VERSION FINALE CORRIGÉE"""

    def __init__(self, message_bus: MessageBus):
        self.bus = message_bus
        self.moderator = DebateModerator()
        self.voting_system = VotingSystem()
        self.active_debates = {}
        self.debate_results = {}

        # Enregistrer le modérateur sur le bus
        self.bus.register_agent(self.moderator)

        # ⚡ CORRECTION: Configurer les abonnements
        self.bus.subscribe("Moderator", "DEBATE_CONCLUSION")
        self.bus.subscribe("Moderator", "ARGUMENT_SUBMISSION")

        logger.info("🎭 DebateManager initialized with moderator")

    def initiate_debate(self, topic: str, question: str, participant_types: List[str]) -> str:
        """Initie un débat complet - VERSION CORRIGÉE"""

        try:
            logger.info(f"🎭 Initiating debate: {topic}")
            logger.info(f"📝 Question: {question}")
            logger.info(f"👥 Requested participant types: {participant_types}")

            # Sélectionner participants
            participants = self.select_participants(participant_types)

            if len(participants) < 2:
                logger.error("❌ Not enough participants for debate")
                return None

            logger.info(f"🎯 Selected participants: {participants}")

            # Créer le débat via le moderateur
            debate_id = self.moderator.create_debate(topic, question, participants)

            if not debate_id:
                logger.error("❌ Failed to create debate")
                return None

            # Stocker les infos
            self.active_debates[debate_id] = {
                "topic": topic,
                "question": question,
                "participants": participants,
                "start_time": datetime.now(),
                "status": "active"
            }

            logger.success(f"✅ Debate created successfully: {debate_id}")
            logger.info(f"👥 Participants: {participants}")

            return debate_id

        except Exception as e:
            logger.error(f"❌ Error initiating debate: {e}")
            return None

    def select_participants(self, types: List[str]) -> List[str]:
        """Sélectionne participants pour le débat - VERSION CORRIGÉE AVEC LOGS DÉTAILLÉS"""

        logger.info(f"🔍 Selecting participants for debate, types requested: {types}")

        available_agents = []

        # Lister tous les agents disponibles
        all_agents = list(self.bus.agents.keys())
        logger.info(f"📝 Available agents in bus: {all_agents}")

        for agent_name, agent in self.bus.agents.items():
            # Vérifier capacité de débat
            has_debate_capability = hasattr(agent, 'participate_in_debate') or hasattr(agent, 'handle_debate_invitation')
            logger.info(f"  • {agent_name} ({getattr(agent, 'role', 'Unknown')}): debate_capability = {has_debate_capability}")

            if not has_debate_capability:
                logger.info(f"    ❌ Skipped {agent_name} (no debate capability)")
                continue

            # Vérifier correspondance de type
            agent_role = getattr(agent, 'role', '').lower()
            agent_name_lower = agent_name.lower()

            type_match = False
            for req_type in types:
                req_type_lower = req_type.lower()
                if (req_type_lower in agent_role or 
                    req_type_lower in agent_name_lower or
                    (req_type_lower == 'worker' and 'worker' in agent_role)):
                    type_match = True
                    break

            if type_match:
                available_agents.append(agent_name)
                logger.info(f"    ✅ Added {agent_name} (role match)")
            else:
                logger.info(f"    ❌ Skipped {agent_name} (no type match)")

        logger.info(f"🎯 Selected participants: {available_agents}")

        # Limiter à un nombre raisonnable (2-5 participants)
        if len(available_agents) > 5:
            available_agents = available_agents[:5]
            logger.info(f"🔄 Limited to 5 participants: {available_agents}")

        logger.success(f"✅ Final selection: {available_agents}")
        return available_agents

    def process_debate_round(self, debate_id: str):
        """Traite un round de débat - NOUVELLE FONCTION"""

        try:
            if debate_id not in self.active_debates:
                logger.error(f"Unknown debate: {debate_id}")
                return

            # Vérifier statut avec le moderateur
            status = self.moderator.get_debate_status(debate_id)

            if not status:
                logger.warning(f"No status available for debate {debate_id}")
                return

            logger.info(f"🔍 Processing debate {debate_id}, status: {status.get('status', 'unknown')}")

            # Le moderateur gère automatiquement la progression
            # Cette fonction peut être utilisée pour monitoring ou intervention manuelle

        except Exception as e:
            logger.error(f"Error processing debate round {debate_id}: {e}")

    def get_debate_status(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Retourne le statut d'un débat"""

        if debate_id not in self.active_debates:
            return None

        # Combiner infos locales et moderateur
        local_info = self.active_debates[debate_id]
        moderator_status = self.moderator.get_debate_status(debate_id)

        if moderator_status:
            local_info.update(moderator_status)

        return local_info

    def handle_debate_conclusion(self, message: Message):
        """Traite la conclusion d'un débat"""

        try:
            result = message.content
            debate_id = result.get("debate_id")

            logger.info(f"🏁 Debate conclusion received for {debate_id}")

            if debate_id in self.active_debates:
                # Mettre à jour statut
                self.active_debates[debate_id]["status"] = "concluded"
                self.active_debates[debate_id]["end_time"] = datetime.now()

                # Stocker résultat
                self.debate_results[debate_id] = result

                # ⚡ CORRECTION CRITIQUE: Envoyer résultat à l'utilisateur
                self._send_result_to_user(debate_id, result)

                # Nettoyer
                del self.active_debates[debate_id]

                logger.success(f"✅ Debate {debate_id} concluded and result sent")

        except Exception as e:
            logger.error(f"Error handling debate conclusion: {e}")

    def _send_result_to_user(self, debate_id: str, result: Dict[str, Any]):
        """Envoie le résultat du débat à l'utilisateur - NOUVELLE FONCTION CRITIQUE"""

        try:
            # Formater le résultat pour l'utilisateur
            synthesis = result.get("synthesis", "Débat terminé")
            topic = result.get("topic", "Sujet inconnu")
            participants = result.get("participants", [])
            rounds = result.get("rounds", 0)
            consensus = result.get("consensus", False)
            points_accord = result.get("points_accord", [])
            points_desaccord = result.get("points_désaccord", [])

            # Construire message détaillé
            user_message = f"""🏁 **RÉSULTAT DU DÉBAT**

📋 **Sujet :** {topic}
👥 **Participants :** {', '.join(participants)}
🔄 **Rounds :** {rounds}
🤝 **Consensus :** {'Oui' if consensus else 'Non'}

📝 **Synthèse :**
{synthesis}

✅ **Points d'accord :**
{chr(10).join(f"• {point}" for point in points_accord) if points_accord else "• Aucun consensus explicite"}

⚠️ **Points de désaccord :**
{chr(10).join(f"• {point}" for point in points_desaccord) if points_desaccord else "• Aucun désaccord majeur identifié"}

🎯 **Recommandation finale disponible.**
"""

            # Envoyer via le Chef (qui communique avec l'utilisateur)
            result_message = Message(
                sender="DebateManager",
                recipient="Chef",
                type="DEBATE_RESULT",
                content={
                    "debate_id": debate_id,
                    "user_message": user_message,
                    "raw_result": result,
                    "for_user": True
                }
            )

            self.bus.publish(result_message)
            logger.info(f"📤 Debate result sent to Chef for user delivery")

        except Exception as e:
            logger.error(f"Error sending result to user: {e}")

    def get_all_active_debates(self) -> Dict[str, Dict[str, Any]]:
        """Retourne tous les débats actifs"""
        return self.active_debates.copy()

    def get_debate_result(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Retourne le résultat d'un débat terminé"""
        return self.debate_results.get(debate_id)

    def cleanup_old_debates(self, max_age_hours: int = 24):
        """Nettoie les vieux débats"""

        current_time = datetime.now()
        to_remove = []

        for debate_id, info in self.active_debates.items():
            age = current_time - info["start_time"]
            if age.total_seconds() > max_age_hours * 3600:
                to_remove.append(debate_id)

        for debate_id in to_remove:
            logger.info(f"🧹 Cleaning up old debate: {debate_id}")
            del self.active_debates[debate_id]

            # Nettoyer aussi du moderateur si possible
            if hasattr(self.moderator, 'active_debates') and debate_id in self.moderator.active_debates:
                del self.moderator.active_debates[debate_id]
