from core.base import BaseAgent, Message
from typing import Optional, Dict, Any
import ollama
import json
from loguru import logger

class BaseWorker(BaseAgent):
    """Classe de base pour tous les agents workers"""

    def __init__(self, name: str, specialty: str):
        super().__init__(name, f"Worker_{specialty}")
        self.specialty = specialty
        self.skills = []
        self.completed_tasks = 0
        self.success_rate = 1.0

        # Configuration spécifique au worker
        self.config = self._get_worker_config()

        # Prompt de base (à surcharger)
        self.prompt_template = self._get_prompt_template()

        # Handlers
        self.message_handlers.update({
            "TASK_ASSIGNMENT": self.handle_task_assignment,
            "CODE_TASK": self.handle_code_task,
            "ANALYSIS_TASK": self.handle_analysis_task
        })

    def _get_worker_config(self) -> Dict[str, Any]:
        """Configuration par défaut du worker"""
        return {
            "model": "llama3.2",
            "temperature": 0.7,
            "max_retries": 3,
            "timeout": 30
        }

    def _get_prompt_template(self) -> str:
        """Template de prompt par défaut"""
        return """Tu es un agent spécialisé en {specialty}.

Tâche : {task}
Type : {task_type}
Critères de succès : {criteria}

Instructions :
1. Analyse la demande avec attention
2. Applique tes compétences spécialisées
3. Produis un résultat de haute qualité
4. Vérifie que tous les critères sont remplis

{additional_context}

Réponds de manière structurée et professionnelle."""

    def handle_task_assignment(self, message: Message) -> Optional[Message]:
        """Traite une assignation de tâche générique"""

        task_info = message.content
        task_type = task_info.get("type", "general")

        logger.info(f"{self.name} received {task_type} task")

        # Router vers le bon handler
        if task_type == "code":
            return self.handle_code_task(message)
        elif task_type == "analysis":
            return self.handle_analysis_task(message)
        else:
            return self.handle_general_task(message)

    def handle_general_task(self, message: Message) -> Message:
        """Traite une tâche générale"""

        task_info = message.content

        try:
            # Exécuter la tâche
            result = self.execute_task(
                task=task_info["task"],
                context={
                    "type": task_info.get("type", "general"),
                    "criteria": task_info.get("criteria", [])
                }
            )

            # Mettre à jour les stats
            self.completed_tasks += 1

            # Retourner le résultat
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="TASK_RESULT",
                content={
                    "status": "completed",
                    "result": result,
                    "subtask_id": task_info.get("subtask_id"),
                    "project_id": task_info.get("project_id"),
                    "worker": self.name
                }
            )

        except Exception as e:
            logger.error(f"{self.name} task failed: {e}")

            # Mettre à jour le taux de succès
            self.success_rate = (self.completed_tasks / 
                               (self.completed_tasks + 1))

            return Message(
                sender=self.name,
                recipient=message.sender,
                type="TASK_RESULT",
                content={
                    "status": "failed",
                    "error": str(e),
                    "subtask_id": task_info.get("subtask_id"),
                    "project_id": task_info.get("project_id")
                }
            )

    def execute_task(self, task: str, context: Dict[str, Any]) -> str:
        """Exécute une tâche avec le LLM"""

        prompt = self.prompt_template.format(
            specialty=self.specialty,
            task=task,
            task_type=context.get("type", "general"),
            criteria="".join(f"- {c}" for c in context.get("criteria", [])),
            additional_context=self._get_additional_context(context)
        )

        # AJOUT : Client Ollama avec host explicite
        import ollama
        client = ollama.Client(host='http://localhost:11434')

        response = client.generate(
            model=self.config["model"],
            prompt=prompt,
            options={
                "temperature": self.config["temperature"],
                "num_predict": 1024
            }
        )

        return response['response']

    def _get_additional_context(self, context: Dict[str, Any]) -> str:
        """Contexte additionnel spécifique au worker"""
        return ""

    def handle_code_task(self, message: Message) -> Message:
        """Handler pour les tâches de code (à surcharger)"""
        return self.handle_general_task(message)

    def handle_analysis_task(self, message: Message) -> Message:
        """Handler pour les tâches d'analyse (à surcharger)"""
        return self.handle_general_task(message)

    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Processus de réflexion du worker"""
        return {
            "thought": f"Processing task as {self.specialty} specialist",
            "confidence": self.success_rate,
            "approach": "standard"
        }

    def process_message(self, message: Message) -> Optional[Message]:
        """Traite les messages entrants"""
        handler = self.message_handlers.get(message.type)
        if handler:
            return handler(message)

        logger.warning(f"No handler for message type: {message.type}")
        return None
