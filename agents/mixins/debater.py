from typing import Dict, Any, List, Optional
from core.debate import Argument
from core.ollama_client import generate
from core.base import Message  # ⚡ CORRECTION: Import Message
import json
from loguru import logger

class DebaterMixin:
    """Mixin pour donner capacité de débat à n'importe quel agent - VERSION FINALE CORRIGÉE"""

    def __init__(self):
        self.debate_prompt_template = """Tu participes à un débat professionnel sur : {topic}
Question : {question}

Ton rôle : {role}
Ta spécialité : {specialty}

Arguments des autres participants :
{other_arguments}

Formule ton argument en tenant compte :
1. De ta perspective unique et expertise
2. Des arguments déjà présentés
3. Des faits et de la logique
4. De la recherche de solution constructive

Réponds UNIQUEMENT en JSON valide :
{{
    "position": "favorable|défavorable|nuancé",
    "argument_principal": "ton argument clé en une phrase",
    "raisonnement": "explication détaillée de ton point de vue",
    "evidence": ["fait1", "fait2", "fait3"],
    "contre_arguments": {{"participant": "réponse à leurs points"}}
}}"""

    def participate_in_debate(self, debate_context: Dict[str, Any]) -> Dict[str, Any]:
        """Participe à un débat - MÉTHODE CORRIGÉE COMPLÈTEMENT"""

        try:
            # Préparer contexte
            other_args = self._summarize_other_arguments(debate_context.get("arguments", []))

            prompt = self.debate_prompt_template.format(
                topic=debate_context.get("topic", "Sujet non spécifié"),
                question=debate_context.get("question", "Question non spécifiée"),
                role=getattr(self, 'role', 'Participant'),
                specialty=getattr(self, 'specialty', 'Généraliste'),
                other_arguments=other_args
            )

            logger.info(f"🎭 {getattr(self, 'name', 'Agent')} participating in debate")

            # Générer argument avec Ollama
            response = generate("llama3.2", prompt)

            # ⚡ CORRECTION CRITIQUE: Convertir response en string
            try:
                response_text = str(response) if hasattr(response, '__str__') else response
                arg_data = json.loads(response_text)

            except json.JSONDecodeError:
                # Fallback si JSON invalide
                logger.warning(f"⚠️ Invalid JSON from {getattr(self, 'name', 'Agent')}, using fallback")
                arg_data = {
                    "position": "nuancé",
                    "argument_principal": "Analyse approfondie nécessaire",
                    "raisonnement": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "evidence": ["Expérience pratique", "Analyse contextuelle"],
                    "contre_arguments": {}
                }

            logger.success(f"✅ {getattr(self, 'name', 'Agent')} provided argument: {arg_data.get('position', 'unknown')}")

            return arg_data

        except Exception as e:
            logger.error(f"❌ Error in debate participation for {getattr(self, 'name', 'Agent')}: {e}")

            # Fallback argument robuste
            return {
                "position": "nuancé",
                "argument_principal": f"Point de vue de {getattr(self, 'specialty', 'expert')}",
                "raisonnement": "Analyse basée sur l'expérience et les meilleures pratiques du domaine",
                "evidence": ["Expérience professionnelle", "Standards de l'industrie", "Best practices"],
                "contre_arguments": {}
            }

    def vote_on_arguments(self, arguments: List[Dict[str, Any]]) -> Dict[str, float]:
        """Évalue et vote sur les arguments"""
        scores = {}

        for i, arg in enumerate(arguments):
            try:
                score = self._evaluate_argument(arg)
                scores[f"arg_{i}"] = score
                logger.info(f"📊 {getattr(self, 'name', 'Agent')} scored arg_{i}: {score}")
            except Exception as e:
                logger.error(f"❌ Error evaluating argument {i}: {e}")
                scores[f"arg_{i}"] = 0.5  # Score neutre

        return scores

    def _evaluate_argument(self, argument: Dict[str, Any]) -> float:
        """Évalue un argument sur plusieurs critères"""
        try:
            criteria = {
                "logique": self._evaluate_logic(argument),
                "evidence": min(len(argument.get("evidence", [])) / 3, 1.0),  # Max 3 evidences
                "clarté": self._evaluate_clarity(argument),
                "pertinence": self._evaluate_relevance(argument)
            }

            # Moyenne pondérée
            weights = {"logique": 0.4, "evidence": 0.3, "clarté": 0.2, "pertinence": 0.1}

            score = sum(criteria[c] * weights[c] for c in criteria)
            return min(1.0, max(0.0, score))

        except Exception as e:
            logger.error(f"❌ Error in argument evaluation: {e}")
            return 0.5

    def _evaluate_logic(self, argument: Dict[str, Any]) -> float:
        """Évalue la logique d'un argument"""
        reasoning = argument.get("raisonnement", "")
        if not reasoning:
            return 0.3

        # Critères simples : longueur et mots-clés logiques
        logic_keywords = ["parce que", "car", "donc", "ainsi", "par conséquent", "en effet", "cependant", "néanmoins"]
        logic_score = len([w for w in logic_keywords if w in reasoning.lower()]) / len(logic_keywords)
        length_score = min(len(reasoning) / 200, 1.0)

        return (logic_score + length_score) / 2

    def _evaluate_clarity(self, argument: Dict[str, Any]) -> float:
        """Évalue la clarté d'un argument"""
        arg_text = argument.get("argument_principal", "")
        if not arg_text:
            return 0.3

        # Critères simples : longueur appropriée, pas trop de jargon
        if 10 <= len(arg_text) <= 150:
            return 0.8
        elif len(arg_text) < 10:
            return 0.3
        else:
            return 0.6

    def _evaluate_relevance(self, argument: Dict[str, Any]) -> float:
        """Évalue la pertinence d'un argument"""
        # Pour l'instant, score basique basé sur la présence de contenu
        has_main_arg = bool(argument.get("argument_principal"))
        has_reasoning = bool(argument.get("raisonnement"))
        has_evidence = len(argument.get("evidence", [])) > 0

        score = sum([has_main_arg, has_reasoning, has_evidence]) / 3
        return max(0.3, score)

    def _summarize_other_arguments(self, arguments: List[Dict[str, Any]]) -> str:
        """Résume les arguments des autres participants"""

        if not arguments:
            return "Aucun argument présenté pour l'instant."

        summary_parts = []
        for i, arg in enumerate(arguments[:3], 1):  # Max 3 arguments pour éviter les prompts trop longs
            participant = arg.get("participant", f"Participant {i}")
            argument = arg.get("argument", arg.get("argument_principal", "Argument non disponible"))
            position = arg.get("position", "non spécifiée")

            summary_parts.append(f"{i}. {participant} ({position}): {argument}")

        return "\n".join(summary_parts)

    def handle_debate_invitation(self, message) -> Optional[Message]:
        """Gère une invitation à un débat - CORRIGÉ POUR RETOURNER MESSAGE"""

        debate_info = message.content
        logger.info(f"🎭 {getattr(self, 'name', 'Agent')} invited to debate: {debate_info.get('topic', 'Unknown')}")

        # ⚡ CORRECTION CRITIQUE: Retourner un objet Message au lieu de dict
        return Message(
            sender=getattr(self, 'name', 'Agent'),
            recipient=message.sender,
            type="DEBATE_ACCEPTANCE",
            content={
                "debate_id": debate_info.get("debate_id"),
                "status": "accepted",
                "participant": getattr(self, 'name', 'Agent')
            }
        )

    def handle_argument_request(self, message) -> Optional[Message]:
        """Gère une demande d'argument - CORRIGÉ POUR RETOURNER MESSAGE"""

        debate_context = message.content

        try:
            # Participer au débat
            argument = self.participate_in_debate(debate_context)

            # ⚡ CORRECTION CRITIQUE: Retourner un objet Message au lieu de dict
            return Message(
                sender=getattr(self, 'name', 'Agent'),
                recipient=message.sender,
                type="ARGUMENT_SUBMISSION",
                content={
                    "debate_id": debate_context.get("debate_id"),
                    "argument": argument,
                    "participant": getattr(self, 'name', 'Agent')
                }
            )

        except Exception as e:
            logger.error(f"❌ Error handling argument request: {e}")

            # Fallback argument
            return Message(
                sender=getattr(self, 'name', 'Agent'),
                recipient=message.sender,
                type="ARGUMENT_SUBMISSION",
                content={
                    "debate_id": debate_context.get("debate_id"),
                    "argument": {
                        "position": "nuancé",
                        "argument_principal": "Erreur lors de la génération d'argument",
                        "raisonnement": f"Désolé, j'ai rencontré un problème: {str(e)}",
                        "evidence": ["Problème technique"],
                        "contre_arguments": {}
                    },
                    "participant": getattr(self, 'name', 'Agent')
                }
            )

    def handle_vote_request(self, message) -> Optional[Message]:
        """Gère une demande de vote - CORRIGÉ POUR RETOURNER MESSAGE"""

        vote_info = message.content
        arguments = vote_info.get("arguments", [])

        try:
            # Voter sur les arguments
            votes = self.vote_on_arguments(arguments)

            # ⚡ CORRECTION CRITIQUE: Retourner un objet Message au lieu de dict
            return Message(
                sender=getattr(self, 'name', 'Agent'),
                recipient=message.sender,
                type="VOTE_SUBMISSION",
                content={
                    "debate_id": vote_info.get("debate_id"),
                    "votes": votes,
                    "voter": getattr(self, 'name', 'Agent')
                }
            )

        except Exception as e:
            logger.error(f"❌ Error handling vote request: {e}")

            # Vote par défaut
            return Message(
                sender=getattr(self, 'name', 'Agent'),
                recipient=message.sender,
                type="VOTE_SUBMISSION",
                content={
                    "debate_id": vote_info.get("debate_id"),
                    "votes": {},
                    "voter": getattr(self, 'name', 'Agent'),
                    "error": str(e)
                }
            )
