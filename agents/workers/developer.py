from core.base import BaseAgent, Message
from typing import Optional, Dict, Any, List
import ollama
import json
import re
from datetime import datetime
from loguru import logger

class DeveloperAgent(BaseAgent):
    """Agent Développeur capable de générer du vrai code"""

    def __init__(self, name: str = "Developer1"):
        super().__init__(name, "Worker_development")
        self.skills = ["python", "javascript", "sql", "bash", "html/css"]
        self.completed_tasks = 0
        self.success_rate = 1.0

        self.code_generation_prompt = """Tu es un développeur Python expert.

Tâche : {task}

Instructions spécifiques :
1. Génère du code Python propre et fonctionnel
2. Ajoute des commentaires explicatifs
3. Inclus la gestion d'erreurs appropriée
4. Utilise des type hints quand c'est pertinent
5. Ajoute une docstring pour chaque fonction/classe

Contraintes :
- Le code doit être immédiatement exécutable
- Pas de dépendances externes sauf si explicitement demandées
- Suit les conventions PEP 8

Génère UNIQUEMENT le code Python, sans explications avant ou après :
"""

        self.code_analysis_prompt = """Analyse ce code et identifie :
1. Ce que fait le code
2. Points forts
3. Points d'amélioration
4. Bugs potentiels
5. Suggestions d'optimisation

Code à analyser :
{code}

Réponds en JSON :
{{
    "description": "ce que fait le code",
    "points_forts": ["point1", "point2"],
    "ameliorations": ["suggestion1", "suggestion2"],
    "bugs_potentiels": ["bug1", "bug2"],
    "complexite": "simple|moyenne|complexe",
    "qualite_globale": 0.0-1.0
}}"""

        self.message_handlers.update({
            "TASK_ASSIGNMENT": self.handle_task_assignment,
            "CODE_REVIEW_REQUEST": self.handle_code_review,
            "DEBUG_REQUEST": self.handle_debug_request
        })

    def handle_task_assignment(self, message: Message) -> Optional[Message]:
        """Traite une assignation de tâche"""

        task_info = message.content
        task = task_info.get("task", "")
        task_type = task_info.get("type", "code")

        logger.info(f"{self.name} received task: {task[:50]}...")

        try:
            if task_type == "code":
                result = self._generate_code(task)
            elif task_type == "analyse":
                result = self._analyze_code(task)
            elif task_type == "debug":
                result = self._debug_code(task)
            else:
                result = self._handle_generic_task(task)

            # Succès
            self.completed_tasks += 1

            return Message(
                sender=self.name,
                recipient=message.sender,
                type="TASK_RESULT",
                content={
                    "status": "completed",
                    "result": result,
                    "project_id": task_info.get("project_id"),
                    "original_requester": task_info.get("original_requester"),
                    "execution_time": datetime.now().isoformat(),
                    "confidence": 0.9
                }
            )

        except Exception as e:
            logger.error(f"{self.name} task failed: {e}")
            self.success_rate = self.completed_tasks / (self.completed_tasks + 1)

            return Message(
                sender=self.name,
                recipient=message.sender,
                type="TASK_RESULT",
                content={
                    "status": "failed",
                    "error": str(e),
                    "project_id": task_info.get("project_id")
                }
            )

    def _generate_code(self, task: str) -> str:
        """Génère du code selon la tâche"""

        # Déterminer le type de code demandé
        code_type = self._identify_code_type(task)

        # Adapter le prompt selon le type
        if "fonction" in task.lower():
            return self._generate_function(task)
        elif "classe" in task.lower():
            return self._generate_class(task)
        elif "script" in task.lower():
            return self._generate_script(task)
        else:
            return self._generate_generic_code(task)

    def _generate_function(self, task: str) -> str:
        """Génère une fonction Python"""

        prompt = self.code_generation_prompt.format(task=task)

        response = ollama.generate(
            model="llama3.2",
            prompt=prompt,
            options={
                "temperature": 0.3,  # Plus bas pour du code
                "top_p": 0.9,
                "num_predict": 1024
            }
        )

        code = response['response']

        # Nettoyer le code
        code = self._clean_code_output(code)

        # Valider
        if self._validate_python_syntax(code):
            return code
        else:
            # Essayer de corriger
            return self._fix_syntax_errors(code)

    def _generate_class(self, task: str) -> str:
        """Génère une classe Python"""

        enhanced_prompt = self.code_generation_prompt.format(task=task)
        enhanced_prompt += "\nLa classe doit inclure : __init__, méthodes principales, docstrings, et type hints."

        response = ollama.generate(
            model="llama3.2",
            prompt=enhanced_prompt,
            options={"temperature": 0.3}
        )

        return self._clean_code_output(response['response'])

    def _generate_script(self, task: str) -> str:
        """Génère un script complet"""

        enhanced_prompt = f"""Génère un script Python complet et exécutable.

Tâche : {task}

Le script doit inclure :
- Shebang (#!/usr/bin/env python3)
- Imports nécessaires
- Fonction main()
- Gestion des arguments si pertinent
- if __name__ == "__main__":

Génère UNIQUEMENT le code :
"""

        response = ollama.generate(
            model="llama3.2",
            prompt=enhanced_prompt,
            options={"temperature": 0.3}
        )

        return self._clean_code_output(response['response'])

    def _analyze_code(self, code: str) -> Dict[str, Any]:
        """Analyse du code fourni"""

        prompt = self.code_analysis_prompt.format(code=code)

        response = ollama.generate(
            model="llama3.2",
            prompt=prompt,
            format="json"
        )

        try:
            analysis = json.loads(response['response'])

            # Ajouter métriques basiques
            analysis['metrics'] = {
                'lines': len(code.split('\n')),
                'functions': len(re.findall(r'def \w+', code)),
                'classes': len(re.findall(r'class \w+', code)),
                'comments': len(re.findall(r'#.*$', code, re.MULTILINE))
            }

            return analysis

        except json.JSONDecodeError:
            return {
                "description": "Analyse échouée",
                "error": "Impossible de parser la réponse"
            }

    def _clean_code_output(self, code: str) -> str:
        """Nettoie la sortie de code"""

        # Enlever les marqueurs de code markdown
        code = re.sub(r'^```\w*\n', '', code)
        code = re.sub(r'\n```$', '', code)
        code = re.sub(r'^```\w*\s*', '', code)
        code = re.sub(r'\s*```$', '', code)

        # Enlever les explications avant/après
        lines = code.split('\n')

        # Trouver le début du code
        code_start = 0
        for i, line in enumerate(lines):
            if line.strip() and (
                line.startswith('def ') or 
                line.startswith('class ') or
                line.startswith('import ') or
                line.startswith('from ') or
                line.startswith('#!')
            ):
                code_start = i
                break

        # Extraire seulement le code
        code_lines = lines[code_start:]

        return '\n'.join(code_lines).strip()

    def _validate_python_syntax(self, code: str) -> bool:
        """Valide la syntaxe Python"""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            return False

    def _fix_syntax_errors(self, code: str) -> str:
        """Tente de corriger les erreurs de syntaxe basiques"""

        # Corrections communes
        code = re.sub(r':\s*$', ':', code, flags=re.MULTILINE)  # Fix colons
        code = re.sub(r'^(\s*)([^\s])', r'\1\2', code, flags=re.MULTILINE)  # Fix indentation

        # Si toujours invalide, demander une correction au LLM
        if not self._validate_python_syntax(code):
            fix_prompt = f"""Ce code Python a des erreurs de syntaxe :

{code}

Corrige-le pour qu'il soit syntaxiquement valide. Retourne UNIQUEMENT le code corrigé :
"""

            response = ollama.generate(
                model="llama3.2",
                prompt=fix_prompt,
                options={"temperature": 0.1}
            )

            return self._clean_code_output(response['response'])

        return code

    def _identify_code_type(self, task: str) -> str:
        """Identifie le type de code demandé"""

        task_lower = task.lower()

        if "fonction" in task_lower or "function" in task_lower:
            return "function"
        elif "classe" in task_lower or "class" in task_lower:
            return "class"
        elif "script" in task_lower:
            return "script"
        elif "api" in task_lower:
            return "api"
        elif "test" in task_lower:
            return "test"
        else:
            return "generic"

    def _handle_generic_task(self, task: str) -> str:
        """Traite une tâche générique"""

        prompt = f"""Tu es un développeur expert.

Tâche : {task}

Fournis une solution appropriée :
"""

        response = ollama.generate(
            model="llama3.2",
            prompt=prompt
        )

        return response['response']

    def handle_code_review(self, message: Message) -> Message:
        """Effectue une revue de code"""

        code = message.content.get("code", "")
        analysis = self._analyze_code(code)

        return Message(
            sender=self.name,
            recipient=message.sender,
            type="CODE_REVIEW_RESULT",
            content=analysis
        )

    def handle_debug_request(self, message: Message) -> Message:
        """Aide au débogage"""

        code = message.content.get("code", "")
        error = message.content.get("error", "")

        debug_prompt = f"""Debug ce code Python qui produit l'erreur suivante :

Code :
{code}

Erreur :
{error}

Identifie le problème et propose une correction :
"""

        response = ollama.generate(
            model="llama3.2",
            prompt=debug_prompt
        )

        return Message(
            sender=self.name,
            recipient=message.sender,
            type="DEBUG_RESULT",
            content={
                "analysis": response['response'],
                "fixed_code": self._extract_code_from_response(response['response'])
            }
        )

    def _extract_code_from_response(self, response: str) -> Optional[str]:
        """Extrait le code d'une réponse qui contient du texte et du code"""

        # Chercher du code entre ``` 
        code_match = re.search(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)

        # Chercher des lignes qui ressemblent à du code
        lines = response.split('\n')
        code_lines = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith(('def ', 'class ', 'import ', 'from ')):
                in_code_block = True

            if in_code_block:
                if line.strip() == '' and len(code_lines) > 0:
                    # Fin probable du bloc de code
                    break
                code_lines.append(line)

        if code_lines:
            return '\n'.join(code_lines)

        return None

    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Réflexion sur la tâche"""

        return {
            "approach": "Analyse de la tâche et génération de code approprié",
            "confidence": 0.85,
            "estimated_time": "2-5 minutes"
        }

    def process_message(self, message: Message) -> Optional[Message]:
        """Traite les messages entrants"""
        handler = self.message_handlers.get(message.type)
        if handler:
            return handler(message)

        logger.warning(f"No handler for message type: {message.type}")
        return None
