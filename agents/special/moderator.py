from core.base import BaseAgent, Message
from core.debate import Debate, Argument
from typing import Dict, Any, List, Optional
from core.ollama_client import generate
import json
from loguru import logger

class DebateModerator(BaseAgent):
    """Moderator de débat - VERSION CORRIGÉE COMPLÈTE"""

    def __init__(self):
        super().__init__("Moderator", "DebateModerator")
        self.active_debates: Dict[str, Debate] = {}
        self.debate_rounds_status = {}  # Suivi des rounds

        # Template pour analyse de débat
        self.analysis_template = """Tu es modérateur de débat entre agents IA experts.

Débat: {topic}
Question: {question}
Round actuel: {round_number}

Arguments reçus ce round:
{arguments_summary}

Ton rôle:
1. Analyser la qualité des arguments
2. Identifier les points de convergence/divergence  
3. Décider si le débat doit continuer ou se conclure
4. Synthétiser les positions

Réponds en JSON:
{{
    "qualité_arguments": 1-10,
    "consensus_émergent": true/false,
    "points_accord": ["point1", "point2"],
    "points_désaccord": ["point1", "point2"],
    "synthèse": "résumé des positions",
    "action": "continuer|voter|conclure",
    "raison_action": "explication de la décision"
}}"""

        logger.info("🎭 DebateModerator initialized with complete fix")

    def process_message(self, message: Message) -> Optional[Message]:
        """Traite les messages avec handlers complets"""

        try:
            if message.type == "CREATE_DEBATE":
                return self.handle_create_debate(message)
            elif message.type == "START_ROUND":
                return self.handle_start_round(message)
            elif message.type == "SUBMIT_ARGUMENT":
                return self.handle_submit_argument(message)
            elif message.type == "DEBATE_INVITATION":
                # Le modérateur peut recevoir des accusés de réception
                return self.handle_invitation_ack(message)
            elif message.type == "ARGUMENT_SUBMISSION":
                return self.handle_argument_submission(message)
            else:
                logger.warning(f"Moderator: Unknown message type {message.type}")
                return None

        except Exception as e:
            logger.error(f"Moderator error processing {message.type}: {e}")
            return None

    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse et décision du modérateur"""

        try:
            prompt = self.analysis_template.format(**context)

            response = generate("llama3.2", prompt)
            response_text = str(response) if hasattr(response, '__str__') else response

            analysis = json.loads(response_text)
            logger.debug(f"Moderator analysis: {analysis}")
            return analysis

        except Exception as e:
            logger.error(f"Moderator thinking error: {e}")
            return {
                "qualité_arguments": 5,
                "consensus_émergent": False,
                "action": "continuer",
                "raison_action": "Analyse par défaut suite à erreur"
            }

    def create_debate(self, topic: str, question: str, participants: List[str]) -> str:
        """Crée un débat - VERSION CORRIGÉE"""

        try:
            # Créer débat
            debate = Debate(topic, question)
            debate.moderator = self.name

            # Ajouter participants
            for participant in participants:
                debate.add_participant(participant)

            # Stocker
            self.active_debates[debate.id] = debate

            # Initialiser suivi
            self.debate_rounds_status[debate.id] = {
                "participants_invited": [],
                "participants_responded": [],
                "arguments_received": [],
                "round_complete": False
            }

            logger.info(f"✅ Created debate {debate.id} with {len(participants)} participants")

            # ⚡ CORRECTION CRITIQUE: Démarrer le premier round IMMÉDIATEMENT
            self.start_round(debate.id)

            return debate.id

        except Exception as e:
            logger.error(f"Error creating debate: {e}")
            return None

    def start_round(self, debate_id: str):
        """Démarre un round - VERSION CORRIGÉE AVEC INVITATIONS"""

        try:
            if debate_id not in self.active_debates:
                logger.error(f"Debate {debate_id} not found")
                return

            debate = self.active_debates[debate_id]
            current_round = debate.start_round()

            logger.info(f"🎭 Starting round {current_round.number} for debate {debate_id}")

            # Réinitialiser le suivi du round
            self.debate_rounds_status[debate_id] = {
                "participants_invited": [],
                "participants_responded": [],
                "arguments_received": [],
                "round_complete": False
            }

            # ⚡ CORRECTION CRITIQUE: ENVOYER LES INVITATIONS MAINTENANT
            self._send_debate_invitations(debate_id)

        except Exception as e:
            logger.error(f"Error starting round for {debate_id}: {e}")

    def _send_debate_invitations(self, debate_id: str):
        """Envoie les invitations de débat - NOUVELLE FONCTION CRITIQUE"""

        try:
            debate = self.active_debates[debate_id]
            current_round = debate.rounds[-1] if debate.rounds else None

            if not current_round:
                logger.error(f"No current round for debate {debate_id}")
                return

            logger.info(f"📨 Sending invitations for debate {debate_id} round {current_round.number}")

            # Préparer le contexte du débat
            debate_context = {
                "debate_id": debate_id,
                "topic": debate.topic,
                "question": debate.question,
                "round": current_round.number,
                "participants": debate.participants.copy(),
                "arguments": self._get_previous_arguments(debate)
            }

            # Envoyer invitation à chaque participant
            for participant in debate.participants:
                invitation = Message(
                    sender=self.name,
                    recipient=participant,
                    type="DEBATE_INVITATION",
                    content=debate_context
                )

                # ⚡ CORRECTION CRITIQUE: ENVOYER VIA LE BUS
                self.send_message(invitation)
                self.debate_rounds_status[debate_id]["participants_invited"].append(participant)

                logger.info(f"📨 Invitation sent to {participant} for debate {debate_id}")

            logger.success(f"✅ All invitations sent for debate {debate_id}")

        except Exception as e:
            logger.error(f"Error sending invitations for {debate_id}: {e}")

    def handle_invitation_ack(self, message: Message) -> Optional[Message]:
        """Gère les accusés de réception d'invitation"""

        debate_id = message.content.get("debate_id")
        participant = message.sender

        if debate_id in self.debate_rounds_status:
            if participant not in self.debate_rounds_status[debate_id]["participants_responded"]:
                self.debate_rounds_status[debate_id]["participants_responded"].append(participant)
                logger.info(f"📬 {participant} acknowledged invitation for debate {debate_id}")

        return None

    def handle_argument_submission(self, message: Message) -> Optional[Message]:
        """Gère la soumission d'arguments"""

        try:
            debate_id = message.content.get("debate_id")
            argument_data = message.content.get("argument", {})
            participant = message.sender

            if debate_id not in self.active_debates:
                logger.error(f"Unknown debate {debate_id}")
                return None

            debate = self.active_debates[debate_id]
            current_round = debate.rounds[-1] if debate.rounds else None

            if not current_round:
                logger.error(f"No active round for debate {debate_id}")
                return None

            # Créer l'argument
            argument = Argument(
                position=argument_data.get("position", "neutral"),
                reasoning=argument_data.get("argument_principal", "") + "\n" + argument_data.get("raisonnement", ""),
                evidence=argument_data.get("evidence", [])
            )

            # Ajouter au round
            current_round.add_argument(participant, argument)

            # Mettre à jour le suivi
            self.debate_rounds_status[debate_id]["arguments_received"].append(participant)

            logger.info(f"📝 Argument received from {participant} for debate {debate_id}")

            # Vérifier si tous ont répondu
            self._check_round_completion(debate_id)

            return None

        except Exception as e:
            logger.error(f"Error handling argument submission: {e}")
            return None

    def _check_round_completion(self, debate_id: str):
        """Vérifie si le round est terminé"""

        try:
            debate = self.active_debates[debate_id]
            round_status = self.debate_rounds_status[debate_id]

            expected_participants = set(debate.participants)
            responded_participants = set(round_status["arguments_received"])

            logger.info(f"🔍 Round check - Expected: {len(expected_participants)}, Received: {len(responded_participants)}")

            if responded_participants >= expected_participants:
                logger.info(f"✅ Round completed for debate {debate_id}")
                self._analyze_and_continue_debate(debate_id)
            else:
                missing = expected_participants - responded_participants
                logger.info(f"⏳ Waiting for arguments from: {missing}")

        except Exception as e:
            logger.error(f"Error checking round completion: {e}")

    def _analyze_and_continue_debate(self, debate_id: str):
        """Analyse le round et décide de la suite"""

        try:
            debate = self.active_debates[debate_id]
            current_round = debate.rounds[-1]

            # Analyser les arguments
            analysis = self.analyze_round(debate_id)

            logger.info(f"🧠 Analysis result for {debate_id}: {analysis.get('action', 'unknown')}")

            # Décider de la suite
            action = analysis.get("action", "conclure")

            if action == "continuer" and len(debate.rounds) < 3:
                logger.info(f"🔄 Starting next round for debate {debate_id}")
                self.start_round(debate_id)
            else:
                logger.info(f"🏁 Concluding debate {debate_id}")
                self.conclude_debate(debate_id, analysis)

        except Exception as e:
            logger.error(f"Error analyzing debate {debate_id}: {e}")
            # Fallback: conclure le débat
            self.conclude_debate(debate_id, {"synthèse": "Débat terminé suite à erreur"})

    def analyze_round(self, debate_id: str) -> Dict[str, Any]:
        """Analyse un round de débat"""

        try:
            debate = self.active_debates[debate_id]
            current_round = debate.rounds[-1] if debate.rounds else None

            if not current_round:
                return {"action": "conclure", "synthèse": "Aucun round actif"}

            # Résumer les arguments
            arguments_summary = self._summarize_round_arguments(current_round)

            # Analyser avec LLM
            analysis = self.think({
                "topic": debate.topic,
                "question": debate.question,
                "round_number": current_round.number,
                "arguments_summary": arguments_summary
            })

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing round: {e}")
            return {"action": "conclure", "synthèse": "Erreur d'analyse"}

    def _summarize_round_arguments(self, round_obj) -> str:
        """Résume les arguments d'un round"""

        if not round_obj.arguments:
            return "Aucun argument reçu"

        summary = []
        for participant, args in round_obj.arguments.items():
            if args:  # Si le participant a des arguments
                arg = args[-1]  # Dernier argument
                summary.append(f"• {participant}: {arg.position} - {arg.reasoning[:100]}...")

        return "\n".join(summary) if summary else "Arguments en attente"

    def conclude_debate(self, debate_id: str, analysis: Dict[str, Any]):
        """Conclut un débat"""

        try:
            debate = self.active_debates[debate_id]

            # Préparer le résultat
            result = {
                "debate_id": debate_id,
                "topic": debate.topic,
                "question": debate.question,
                "rounds": len(debate.rounds),
                "participants": debate.participants,
                "synthesis": analysis.get("synthèse", "Débat terminé"),
                "consensus": analysis.get("consensus_émergent", False),
                "points_accord": analysis.get("points_accord", []),
                "points_désaccord": analysis.get("points_désaccord", [])
            }

            # Conclure le débat
            debate.conclude(result)

            # Nettoyer le suivi
            if debate_id in self.debate_rounds_status:
                del self.debate_rounds_status[debate_id]

            logger.success(f"🏁 Debate {debate_id} concluded successfully")

            # ⚡ ENVOYER LE RÉSULTAT AU DEBATE MANAGER
            conclusion_message = Message(
                sender=self.name,
                recipient="DebateManager",  # Sera routé vers le système
                type="DEBATE_CONCLUSION",
                content=result
            )

            self.send_message(conclusion_message)

        except Exception as e:
            logger.error(f"Error concluding debate {debate_id}: {e}")

    def _get_previous_arguments(self, debate) -> List[Dict]:
        """Récupère les arguments précédents"""

        previous_args = []

        for round_obj in debate.rounds[:-1]:  # Tous sauf le round actuel
            for participant, args in round_obj.arguments.items():
                for arg in args:
                    previous_args.append({
                        "participant": participant,
                        "position": arg.position,
                        "argument": arg.reasoning[:200],
                        "round": round_obj.number
                    })

        return previous_args

    def get_debate_status(self, debate_id: str) -> Optional[Dict]:
        """Retourne le statut d'un débat"""

        if debate_id not in self.active_debates:
            return None

        debate = self.active_debates[debate_id]
        round_status = self.debate_rounds_status.get(debate_id, {})

        return {
            "id": debate_id,
            "status": debate.status,
            "topic": debate.topic,
            "participants": debate.participants,
            "rounds": len(debate.rounds),
            "current_round_status": round_status
        }

    # HANDLERS pour compatibilité
    def handle_create_debate(self, message: Message) -> Optional[Message]:
        """Handler pour création de débat"""
        content = message.content
        debate_id = self.create_debate(
            content["topic"],
            content["question"], 
            content["participants"]
        )

        return Message(
            sender=self.name,
            recipient=message.sender,
            type="DEBATE_CREATED",
            content={"debate_id": debate_id}
        )

    def handle_start_round(self, message: Message) -> None:
        """Handler pour démarrage de round"""
        debate_id = message.content.get("debate_id")
        if debate_id:
            self.start_round(debate_id)
        return None

    def handle_submit_argument(self, message: Message) -> None:
        """Handler pour soumission d'argument"""
        return self.handle_argument_submission(message)
