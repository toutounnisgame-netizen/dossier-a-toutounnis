from agents.chef import AgentChef
from agents.mixins.debater import DebaterMixin
from core.base import Message
from typing import Dict, Any, Optional, List
from loguru import logger

class EnhancedAgentChef(AgentChef, DebaterMixin):
    """Agent Chef amélioré avec capacités de débat - VERSION FINALE CORRIGÉE"""

    def __init__(self):
        AgentChef.__init__(self)
        DebaterMixin.__init__(self)
        self.personality = "strategic_visionary"
        self.debate_manager = None  # Sera défini depuis main
        self.specialty = "leadership"

        logger.info("🎖️ Enhanced Agent Chef initialized with debate capability")

    def process_message(self, message: Message) -> Optional[Message]:
        """Traite les messages avec support débat - CORRIGÉ"""

        try:
            # Messages de débat
            if message.type == "DEBATE_INVITATION":
                return self.handle_debate_invitation(message)
            elif message.type == "REQUEST_ARGUMENT":
                return self.handle_argument_request(message)
            elif message.type == "REQUEST_VOTE":
                return self.handle_vote_request(message)
            elif message.type == "DEBATE_RESULT":
                return self.handle_debate_result(message)
            else:
                # Traitement normal par AgentChef
                return super().process_message(message)

        except Exception as e:
            logger.error(f"Enhanced Chef error processing {message.type}: {e}")
            return self._create_error_response(message, str(e))

    def handle_request(self, message: Message) -> Optional[Message]:
        """Traite une requête utilisateur avec décision de débat - CORRIGÉ COMPLET"""

        if message.sender != "User":
            return super().handle_request(message)

        user_request = message.content.get("request", "")
        logger.info(f"🎖️ Enhanced Chef processing: {user_request[:50]}...")

        try:
            # Analyser avec LLM
            analysis = self.think({"user_request": user_request})

            if not analysis:
                return self._create_error_response(message, "Impossible d'analyser votre demande")

            logger.info(f"📊 Analysis result: {analysis}")

            # Décision : débat nécessaire ?
            should_debate = self.should_initiate_debate(analysis)
            logger.info(f"🤔 Debate needed: {should_debate} (complexity={analysis.get('complexité')}, type={analysis.get('type_tache')})")

            if should_debate and self.debate_manager:
                # Initier un débat
                return self.initiate_debate_for_decision(analysis, message)
            else:
                # Traitement normal
                logger.info("📝 Simple request, processing directly...")
                return self._delegate_or_handle(analysis, message)

        except Exception as e:
            logger.error(f"Error in enhanced request handling: {e}")
            return self._create_error_response(message, f"Erreur lors du traitement: {str(e)}")

    def should_initiate_debate(self, analysis: Dict[str, Any]) -> bool:
        """Détermine si un débat est nécessaire - LOGIQUE AMÉLIORÉE"""

        complexity = analysis.get("complexité", "simple")
        task_type = analysis.get("type_tache", "autre")
        stakes = analysis.get("enjeux", "faibles")

        # Règles de décision pour déclencher un débat
        debate_triggers = {
            "complexité": complexity in ["moyenne", "complexe"],
            "type_tache": task_type in ["recherche", "analyse", "architecture"],
            "enjeux": stakes in ["élevés", "critiques"]
        }

        # Au moins 2 critères doivent être vrais
        trigger_count = sum(debate_triggers.values())

        logger.info(f"🎯 Debate triggers: complexity={debate_triggers['complexité']}, type={debate_triggers['type_tache']}, stakes={debate_triggers['enjeux']}")
        logger.info(f"📊 Trigger count: {trigger_count}/3")

        return trigger_count >= 1  # Débat si au moins 1 critère

    def initiate_debate_for_decision(self, analysis: Dict[str, Any], original_message: Message) -> Optional[Message]:
        """Initie un débat pour une décision complexe - CORRIGÉ COMPLET"""

        try:
            logger.info("🎭 Complex request detected, initiating debate...")

            # Déterminer types de participants
            participant_types = self.select_debate_participants(analysis.get("type_tache", "recherche"))
            logger.info(f"📋 Selected participant types for '{analysis.get('type_tache')}': {participant_types}")

            if not self.debate_manager:
                logger.error("❌ No debate manager available")
                return self._fallback_to_direct_processing(analysis, original_message)

            # Initier le débat
            logger.info(f"🎭 Initiating debate with participant types: {participant_types}")

            debate_id = self.debate_manager.initiate_debate(
                topic=analysis.get("compréhension", "Question de l'utilisateur"),
                question=f"Quelle est la meilleure approche pour : {original_message.content['request']}?",
                participant_types=participant_types
            )

            if not debate_id:
                logger.error("❌ Failed to create debate, falling back to direct processing")
                return self._fallback_to_direct_processing(analysis, original_message)

            logger.success(f"✅ Debate initiated successfully: {debate_id}")

            # Répondre à l'utilisateur
            return Message(
                sender=self.name,
                recipient=original_message.sender,
                type="RESPONSE",
                content={
                    "status": "debate_initiated",
                    "message": f"""🎭 J'ai initié un débat entre experts pour cette question complexe.

📋 Sujet: {analysis.get("compréhension", "Votre demande")}
👥 Participants: Experts en {', '.join(participant_types)}
🎯 Débat ID: {debate_id}

⏳ Les experts vont débattre et je vous donnerai leur recommandation finale.""",
                    "debate_id": debate_id,
                    "analysis": analysis
                },
                thread_id=original_message.id
            )

        except Exception as e:
            logger.error(f"Error initiating debate: {e}")
            return self._fallback_to_direct_processing(analysis, original_message)

    def select_debate_participants(self, task_type: str) -> List[str]:
        """Sélectionne les types de participants pour un débat"""

        participant_mapping = {
            "développement": ["developer", "architect", "worker"],
            "analyse": ["analyst", "researcher", "worker"],
            "recherche": ["research", "researcher", "worker"],
            "architecture": ["architect", "developer", "analyst"],
            "sécurité": ["security", "developer", "analyst"],
            "performance": ["performance", "developer", "analyst"],
            "autre": ["worker", "analyst"]
        }

        return participant_mapping.get(task_type, ["research", "researcher", "worker"])

    def _fallback_to_direct_processing(self, analysis: Dict[str, Any], original_message: Message) -> Message:
        """Traitement direct en cas d'échec de débat"""

        logger.info("🔄 Fallback to direct processing")

        return Message(
            sender=self.name,
            recipient=original_message.sender,
            type="RESPONSE",
            content={
                "status": "processed_directly",
                "message": f"""📋 Analyse de votre demande :

{analysis.get('compréhension', 'Demande analysée')}

🎯 Type de tâche : {analysis.get('type_tache', 'Non défini')}
📊 Complexité : {analysis.get('complexité', 'Non définie')}

Je traite votre demande directement.""",
                "analysis": analysis
            }
        )

    def handle_debate_result(self, message: Message) -> Optional[Message]:
        """Traite le résultat d'un débat - NOUVELLE FONCTION"""

        try:
            result = message.content

            if result.get("for_user", False):
                # Transférer le résultat à l'utilisateur
                return Message(
                    sender=self.name,
                    recipient="User",
                    type="RESPONSE",
                    content={
                        "status": "debate_completed",
                        "message": result.get("user_message", "Débat terminé"),
                        "debate_details": result.get("raw_result", {})
                    }
                )

            return None

        except Exception as e:
            logger.error(f"Error handling debate result: {e}")
            return None

    def _delegate_or_handle(self, analysis: Dict[str, Any], original_message: Message) -> Message:
        """Délègue ou traite selon l'analyse"""

        decision = analysis.get("décision", "traiter_directement")

        if decision == "déléguer":
            # Déléguer au ChefProjet
            return Message(
                sender=self.name,
                recipient="ChefProjet",
                type="TASK_ASSIGNMENT",
                content={
                    "task": analysis.get("instructions_spéciales", original_message.content["request"]),
                    "context": {
                        "original_request": original_message.content["request"],
                        "analysis": analysis,
                        "requester": original_message.sender
                    }
                },
                thread_id=original_message.id
            )
        else:
            # Traiter directement
            return Message(
                sender=self.name,
                recipient=original_message.sender,
                type="RESPONSE",
                content={
                    "status": "completed",
                    "message": f"""✅ J'ai analysé votre demande.

📋 Compréhension : {analysis.get('compréhension', 'Demande comprise')}
🎯 Action : {analysis.get('instructions_spéciales', 'Traitement direct')}

Votre demande a été traitée.""",
                    "analysis": analysis
                },
                thread_id=original_message.id
            )

    def participate_in_debate(self, debate_context: Dict[str, Any]) -> Dict[str, Any]:
        """Participe à un débat en tant que CEO"""

        # Utiliser le mixin pour la participation
        return super().participate_in_debate(debate_context)

    def _create_error_response(self, original_message: Message, error_msg: str) -> Message:
        """Crée une réponse d'erreur"""

        return Message(
            sender=self.name,
            recipient=original_message.sender,
            type="RESPONSE",
            content={
                "status": "error",
                "message": f"❌ Erreur : {error_msg}",
                "error": error_msg
            },
            thread_id=original_message.id
        )

    def _format_other_arguments(self, arguments: List[Dict]) -> str:
        """Formate les autres arguments pour le contexte"""

        if not arguments:
            return "Aucun argument précédent"

        formatted = []
        for arg in arguments[:3]:  # Limiter à 3 arguments
            participant = arg.get("participant", "Inconnu")
            position = arg.get("position", "neutre")
            argument = arg.get("argument", "Argument non disponible")[:100]
            formatted.append(f"• {participant} ({position}): {argument}...")

        return "\n".join(formatted)
