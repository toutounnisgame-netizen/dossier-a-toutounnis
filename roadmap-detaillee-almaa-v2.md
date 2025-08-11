# ROADMAP DÉTAILLÉE - ALMAA v2.0
## Guide de Développement Semaine par Semaine

---

# PHASE 1 : FOUNDATION (SEMAINES 1-4)

## Semaine 1 : Structure de Base

### Jour 1-2 : Setup Projet
```bash
# Structure initiale
mkdir -p almaa/{core,agents,actions,interfaces,utils,tests,docs,config,data,scripts}
cd almaa

# Git init
git init
echo "# ALMAA v2.0" > README.md

# Virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Requirements de base
cat > requirements.txt << EOF
pydantic>=2.0
click>=8.0
pyyaml>=6.0
python-dotenv>=1.0
loguru>=0.7
pytest>=7.0
black>=23.0
ollama
EOF

pip install -r requirements.txt
```

### Jour 3-4 : Classes de Base
**Fichier : core/base.py**
```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
from pydantic import BaseModel

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: str
    recipient: Optional[str] = None
    type: str  # REQUEST, RESPONSE, BROADCAST
    priority: int = 5
    content: Dict[str, Any]
    thread_id: Optional[str] = None

class BaseAgent(ABC):
    def __init__(self, name: str, role: str):
        self.id = str(uuid4())
        self.name = name
        self.role = role
        self.inbox = []
        self.outbox = []
        self.state = "idle"
        
    @abstractmethod
    def process_message(self, message: Message) -> Optional[Message]:
        pass
    
    @abstractmethod
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
```

### Jour 5 : Configuration et Logging
**Fichier : utils/config.py**
```python
import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    def __init__(self, config_path: str = "config/default.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            "system": {
                "name": "ALMAA",
                "version": "2.0",
                "debug": False
            },
            "agents": {
                "max_agents": 20,
                "default_model": "llama3.2"
            },
            "memory": {
                "max_size": 1000000,
                "embedding_model": "all-MiniLM-L6-v2"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
```

**Fichier : utils/logger.py**
```python
from loguru import logger
import sys

def setup_logger(debug: bool = False):
    logger.remove()
    
    # Console logging
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level
    )
    
    # File logging
    logger.add(
        "data/logs/almaa_{time}.log",
        rotation="500 MB",
        retention="7 days",
        level="DEBUG"
    )
    
    return logger
```

## Semaine 2 : Communication et Tests

### Jour 1-2 : Système de Messages
**Fichier : core/communication.py**
```python
from typing import List, Dict, Optional, Callable
from collections import defaultdict
from .base import Message, BaseAgent

class MessageBus:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.subscribers: Dict[str, List[str]] = defaultdict(list)
        self.message_history: List[Message] = []
        self.handlers: Dict[str, Callable] = {}
    
    def register_agent(self, agent: BaseAgent):
        self.agents[agent.name] = agent
        logger.info(f"Agent registered: {agent.name}")
    
    def subscribe(self, agent_name: str, message_type: str):
        self.subscribers[message_type].append(agent_name)
    
    def publish(self, message: Message):
        self.message_history.append(message)
        
        # Direct message
        if message.recipient:
            if message.recipient in self.agents:
                self.agents[message.recipient].inbox.append(message)
        # Broadcast
        else:
            for subscriber in self.subscribers.get(message.type, []):
                if subscriber in self.agents:
                    self.agents[subscriber].inbox.append(message)
    
    def process_messages(self):
        for agent in self.agents.values():
            while agent.inbox:
                message = agent.inbox.pop(0)
                response = agent.process_message(message)
                if response:
                    self.publish(response)
```

### Jour 3-4 : Tests Unitaires
**Fichier : tests/test_communication.py**
```python
import pytest
from core.base import Message, BaseAgent
from core.communication import MessageBus

class MockAgent(BaseAgent):
    def process_message(self, message: Message) -> Optional[Message]:
        if message.type == "PING":
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="PONG",
                content={"response": "pong"}
            )
        return None
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"thought": "test"}

def test_message_bus_registration():
    bus = MessageBus()
    agent = MockAgent("test_agent", "tester")
    
    bus.register_agent(agent)
    
    assert "test_agent" in bus.agents
    assert bus.agents["test_agent"] == agent

def test_direct_messaging():
    bus = MessageBus()
    agent1 = MockAgent("agent1", "tester")
    agent2 = MockAgent("agent2", "tester")
    
    bus.register_agent(agent1)
    bus.register_agent(agent2)
    
    message = Message(
        sender="agent1",
        recipient="agent2",
        type="PING",
        content={"test": "data"}
    )
    
    bus.publish(message)
    assert len(agent2.inbox) == 1
    assert agent2.inbox[0].sender == "agent1"

def test_broadcast_messaging():
    bus = MessageBus()
    agent1 = MockAgent("agent1", "tester")
    agent2 = MockAgent("agent2", "tester")
    agent3 = MockAgent("agent3", "tester")
    
    bus.register_agent(agent1)
    bus.register_agent(agent2)
    bus.register_agent(agent3)
    
    bus.subscribe("agent2", "BROADCAST")
    bus.subscribe("agent3", "BROADCAST")
    
    message = Message(
        sender="agent1",
        type="BROADCAST",
        content={"announcement": "test"}
    )
    
    bus.publish(message)
    
    assert len(agent1.inbox) == 0
    assert len(agent2.inbox) == 1
    assert len(agent3.inbox) == 1
```

### Jour 5 : Documentation
**Fichier : docs/week1-2-summary.md**
```markdown
# Semaines 1-2 : Résumé

## Accompli
- ✅ Structure du projet créée
- ✅ Classes de base (Message, BaseAgent)
- ✅ Système de configuration YAML
- ✅ Logging avec Loguru
- ✅ MessageBus pour communication
- ✅ Tests unitaires de base

## Architecture
```
almaa/
├── core/
│   ├── base.py          # Classes abstraites
│   └── communication.py # MessageBus
├── utils/
│   ├── config.py        # Configuration
│   └── logger.py        # Logging
└── tests/
    └── test_communication.py
```

## Prochaines étapes
- Implémenter premiers agents concrets
- Ajouter interface CLI basique
- Intégrer Ollama pour LLM
```

## Semaine 3 : Premiers Agents

### Jour 1-2 : Agent Chef
**Fichier : agents/chef.py**
```python
from core.base import BaseAgent, Message
from typing import Optional, Dict, Any
import ollama

class AgentChef(BaseAgent):
    def __init__(self):
        super().__init__("Chef", "CEO")
        self.prompt_template = """
Tu es le CEO d'une organisation d'agents IA.

Contexte actuel : {context}

Demande de l'utilisateur : {user_request}

Ton rôle :
1. Comprendre précisément la demande
2. Identifier le type de tâche
3. Décider qui doit s'en occuper
4. Formuler des instructions claires

Réponds en JSON avec la structure :
{{
    "compréhension": "résumé de ce que tu as compris",
    "type_tache": "développement|analyse|recherche|autre",
    "complexité": "simple|moyenne|complexe",
    "délégation": "nom_agent ou 'moi-même'",
    "instructions": "instructions détaillées"
}}
"""
    
    def process_message(self, message: Message) -> Optional[Message]:
        if message.type == "USER_REQUEST":
            return self._handle_user_request(message)
        elif message.type == "TASK_RESULT":
            return self._handle_task_result(message)
        return None
    
    def _handle_user_request(self, message: Message) -> Message:
        # Analyser la demande avec LLM
        analysis = self.think({
            "user_request": message.content.get("request", "")
        })
        
        # Décider de la délégation
        if analysis["délégation"] == "moi-même":
            # Traiter directement
            result = self._process_directly(analysis)
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="RESPONSE",
                content={"result": result}
            )
        else:
            # Déléguer
            return Message(
                sender=self.name,
                recipient=analysis["délégation"],
                type="TASK_ASSIGNMENT",
                content={
                    "task": analysis["instructions"],
                    "original_request": message.content["request"],
                    "requester": message.sender
                }
            )
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.prompt_template.format(
            context=str(context),
            user_request=context.get("user_request", "")
        )
        
        response = ollama.generate(
            model="llama3.2",
            prompt=prompt,
            format="json"
        )
        
        return response['response']
```

### Jour 3 : Agent Chef de Projet
**Fichier : agents/chef_projet.py**
```python
class AgentChefProjet(BaseAgent):
    def __init__(self):
        super().__init__("ChefProjet", "CPO")
        self.current_projects = {}
        self.prompt_template = """
Tu es Chef de Projet dans une organisation d'agents IA.

Tâche reçue : {task}
Contexte : {context}

Ton rôle :
1. Analyser la complexité de la tâche
2. La décomposer en sous-tâches si nécessaire
3. Créer un plan d'action
4. Estimer le temps nécessaire
5. Identifier les ressources/agents nécessaires

Réponds en JSON :
{{
    "analyse": "description de la tâche",
    "complexité": 1-10,
    "sous_taches": [
        {{
            "id": "unique_id",
            "description": "...",
            "agent_type": "développeur|analyste|chercheur",
            "priorité": 1-10,
            "dépendances": []
        }}
    ],
    "temps_estimé": "Xh",
    "plan_action": ["étape 1", "étape 2", ...]
}}
"""
    
    def process_message(self, message: Message) -> Optional[Message]:
        if message.type == "TASK_ASSIGNMENT":
            return self._create_project_plan(message)
        elif message.type == "SUBTASK_COMPLETE":
            return self._handle_subtask_completion(message)
        return None
    
    def _create_project_plan(self, message: Message) -> Message:
        # Analyser avec LLM
        plan = self.think({
            "task": message.content["task"],
            "requester": message.sender
        })
        
        # Créer projet
        project_id = str(uuid4())
        self.current_projects[project_id] = {
            "plan": plan,
            "status": "active",
            "subtasks_completed": []
        }
        
        # Commencer à distribuer les sous-tâches
        if plan["sous_taches"]:
            first_task = plan["sous_taches"][0]
            return Message(
                sender=self.name,
                recipient=f"Manager_{first_task['agent_type']}",
                type="SUBTASK_ASSIGNMENT",
                content={
                    "project_id": project_id,
                    "subtask": first_task,
                    "full_plan": plan
                }
            )
```

### Jour 4 : Agent Worker Simple
**Fichier : agents/workers/developer.py**
```python
class AgentDeveloper(BaseAgent):
    def __init__(self, name: str = "Dev1"):
        super().__init__(name, "Developer")
        self.skills = ["python", "javascript", "sql"]
        self.prompt_template = """
Tu es un développeur dans une équipe d'agents IA.

Tâche : {task}
Langage préféré : {language}

Instructions :
1. Écris du code propre et commenté
2. Gère les erreurs
3. Suis les best practices
4. Ajoute des tests si pertinent

Génère le code demandé :
"""
    
    def process_message(self, message: Message) -> Optional[Message]:
        if message.type == "CODE_TASK":
            code = self._write_code(message.content["task"])
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="CODE_RESULT",
                content={
                    "code": code,
                    "language": "python",
                    "task_id": message.content.get("task_id")
                }
            )
        return None
    
    def _write_code(self, task: str) -> str:
        prompt = self.prompt_template.format(
            task=task,
            language="python"
        )
        
        response = ollama.generate(
            model="llama3.2",
            prompt=prompt
        )
        
        # Extraire le code
        code = response['response']
        
        # Validation basique
        if self._validate_code(code):
            return code
        else:
            # Retry avec corrections
            return self._fix_code(code)
```

### Jour 5 : Interface CLI Basique
**Fichier : interfaces/cli.py**
```python
import click
from core.communication import MessageBus
from agents.chef import AgentChef
from agents.chef_projet import AgentChefProjet

class ALMAACli:
    def __init__(self):
        self.bus = MessageBus()
        self.setup_agents()
    
    def setup_agents(self):
        # Créer agents
        chef = AgentChef()
        chef_projet = AgentChefProjet()
        
        # Enregistrer
        self.bus.register_agent(chef)
        self.bus.register_agent(chef_projet)
        
        # Abonnements
        self.bus.subscribe("ChefProjet", "TASK_ASSIGNMENT")
    
    def send_request(self, request: str):
        message = Message(
            sender="User",
            recipient="Chef",
            type="USER_REQUEST",
            content={"request": request}
        )
        
        self.bus.publish(message)
        self.bus.process_messages()
        
        # Attendre réponse
        for msg in self.bus.message_history:
            if msg.type == "RESPONSE" and msg.recipient == "User":
                return msg.content["result"]

@click.command()
@click.option('--request', '-r', help='Demande à envoyer au système')
def main(request):
    """ALMAA - Système Multi-Agents Autonome"""
    cli = ALMAACli()
    
    if request:
        result = cli.send_request(request)
        click.echo(f"Résultat : {result}")
    else:
        # Mode interactif
        click.echo("🤖 ALMAA v2.0 - Mode Interactif")
        click.echo("Tapez 'exit' pour quitter")
        
        while True:
            user_input = click.prompt("Vous")
            if user_input.lower() == 'exit':
                break
            
            result = cli.send_request(user_input)
            click.echo(f"ALMAA : {result}")

if __name__ == '__main__':
    main()
```

## Semaine 4 : Tests d'Intégration

### Jour 1-2 : Tests Système Complet
**Fichier : tests/test_integration.py**
```python
import pytest
from interfaces.cli import ALMAACli
from core.base import Message

def test_simple_request_flow():
    """Test du flow complet : User -> Chef -> ChefProjet"""
    cli = ALMAACli()
    
    # Envoyer demande
    result = cli.send_request("Crée une fonction pour calculer fibonacci")
    
    # Vérifier que le système a traité la demande
    assert result is not None
    
    # Vérifier l'historique
    messages = cli.bus.message_history
    
    # Should have: USER_REQUEST -> TASK_ASSIGNMENT -> ...
    assert any(m.type == "USER_REQUEST" for m in messages)
    assert any(m.type == "TASK_ASSIGNMENT" for m in messages)

def test_multi_agent_collaboration():
    """Test collaboration entre agents"""
    cli = ALMAACli()
    
    # Ajouter plus d'agents
    from agents.workers.developer import AgentDeveloper
    dev = AgentDeveloper()
    cli.bus.register_agent(dev)
    
    # Demande complexe
    result = cli.send_request("Analyse ce code et propose des améliorations")
    
    # Vérifier interactions
    chef_messages = [m for m in cli.bus.message_history if m.sender == "Chef"]
    assert len(chef_messages) > 0
```

### Jour 3 : Documentation Complète Phase 1
**Fichier : docs/phase1-complete.md**
```markdown
# Phase 1 Complète : Foundation

## ✅ Objectifs Atteints

### Architecture
- Structure modulaire du projet
- Classes de base (Agent, Message)
- Système de communication (MessageBus)
- Configuration flexible (YAML)
- Logging professionnel

### Agents Implémentés
1. **AgentChef** (CEO)
   - Reçoit demandes utilisateur
   - Analyse et délègue
   - Interface principale

2. **AgentChefProjet** (CPO)
   - Planifie projets
   - Décompose en sous-tâches
   - Coordonne exécution

3. **AgentDeveloper** (Worker)
   - Écrit du code
   - Valide syntaxe
   - Retourne résultats

### Interface
- CLI basique fonctionnelle
- Mode interactif
- Commandes directes

### Tests
- Tests unitaires MessageBus
- Tests intégration
- Coverage > 80%

## Métriques
- Lignes de code : ~1,500
- Tests : ~300 lignes
- Documentation : ~200 lignes

## Apprentissages
1. Ollama s'intègre facilement
2. MessageBus simplifie communication
3. Tests critiques dès le début

## Prochaine Phase
Phase 2 : Intelligence (Débats + Mémoire)
```

### Jour 4-5 : Refactoring et Optimisation
```python
# Améliorer performance MessageBus
# Ajouter retry logic
# Optimiser prompt templates
# Nettoyer code
```

---

# PHASE 2 : INTELLIGENCE (SEMAINES 5-8)

## Semaine 5 : Système de Débats - Partie 1

### Jour 1 : Structure de Débat
**Fichier : core/debate.py**
```python
from typing import List, Dict, Optional
from datetime import datetime
from .base import BaseAgent, Message

class Debate:
    def __init__(self, topic: str, question: str):
        self.id = str(uuid4())
        self.topic = topic
        self.question = question
        self.participants: List[str] = []
        self.moderator: Optional[str] = None
        self.rounds: List[DebateRound] = []
        self.status = "open"  # open, active, voting, closed
        self.result = None
        self.created_at = datetime.now()
    
    def add_participant(self, agent_name: str):
        if agent_name not in self.participants:
            self.participants.append(agent_name)
    
    def start_round(self) -> 'DebateRound':
        round_num = len(self.rounds) + 1
        new_round = DebateRound(round_num, self.participants)
        self.rounds.append(new_round)
        self.status = "active"
        return new_round
    
    def close_round(self):
        if self.rounds:
            self.rounds[-1].close()
    
    def start_voting(self):
        self.status = "voting"
    
    def conclude(self, result: Dict[str, Any]):
        self.status = "closed"
        self.result = result

class DebateRound:
    def __init__(self, number: int, participants: List[str]):
        self.number = number
        self.participants = participants
        self.arguments: Dict[str, List[Argument]] = {p: [] for p in participants}
        self.status = "open"
        self.started_at = datetime.now()
        self.closed_at = None
    
    def add_argument(self, participant: str, argument: 'Argument'):
        if participant in self.arguments:
            self.arguments[participant].append(argument)
    
    def close(self):
        self.status = "closed"
        self.closed_at = datetime.now()

class Argument:
    def __init__(self, position: str, reasoning: str, evidence: List[str] = None):
        self.position = position
        self.reasoning = reasoning
        self.evidence = evidence or []
        self.timestamp = datetime.now()
        self.votes = 0
```

### Jour 2 : Moderateur de Débat
**Fichier : agents/special/moderator.py**
```python
class DebateModerator(BaseAgent):
    def __init__(self):
        super().__init__("Moderator", "Debate_Moderator")
        self.active_debates: Dict[str, Debate] = {}
        self.prompt_template = """
Tu es modérateur de débat entre agents IA.

Débat : {topic}
Question : {question}
Tour actuel : {round_number}
Arguments jusqu'ici : {arguments_summary}

Ton rôle :
1. Assurer que le débat reste constructif
2. Identifier les points de convergence/divergence
3. Synthétiser les arguments
4. Proposer la prochaine question si nécessaire

Action à prendre : {action_needed}

Réponds en JSON :
{{
    "synthèse": "résumé des positions",
    "points_accord": ["point1", "point2"],
    "points_désaccord": ["point1", "point2"],
    "prochaine_action": "continuer|voter|conclure",
    "question_suivante": "si pertinent"
}}
"""
    
    def create_debate(self, topic: str, question: str, participants: List[str]) -> str:
        debate = Debate(topic, question)
        debate.moderator = self.name
        
        for participant in participants:
            debate.add_participant(participant)
        
        self.active_debates[debate.id] = debate
        
        # Notifier participants
        for participant in participants:
            self.send_message(Message(
                sender=self.name,
                recipient=participant,
                type="DEBATE_INVITATION",
                content={
                    "debate_id": debate.id,
                    "topic": topic,
                    "question": question,
                    "role": "participant"
                }
            ))
        
        return debate.id
    
    def start_round(self, debate_id: str):
        debate = self.active_debates.get(debate_id)
        if not debate:
            return
        
        round = debate.start_round()
        
        # Demander arguments à chaque participant
        for participant in debate.participants:
            self.send_message(Message(
                sender=self.name,
                recipient=participant,
                type="REQUEST_ARGUMENT",
                content={
                    "debate_id": debate_id,
                    "round": round.number,
                    "question": debate.question,
                    "time_limit": 60  # secondes
                }
            ))
```

### Jour 3 : Mécanique de Vote
**Fichier : core/voting.py**
```python
from typing import Dict, List, Optional
from collections import defaultdict

class VotingSystem:
    def __init__(self):
        self.voting_methods = {
            "majority": self.majority_vote,
            "weighted": self.weighted_vote,
            "ranked": self.ranked_choice_vote,
            "consensus": self.consensus_vote
        }
    
    def conduct_vote(self, 
                    options: List[str], 
                    votes: Dict[str, Any], 
                    method: str = "majority",
                    weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        
        if method not in self.voting_methods:
            raise ValueError(f"Unknown voting method: {method}")
        
        return self.voting_methods[method](options, votes, weights)
    
    def majority_vote(self, options: List[str], votes: Dict[str, str], weights=None):
        """Simple majorité"""
        counts = defaultdict(int)
        
        for voter, choice in votes.items():
            if choice in options:
                counts[choice] += 1
        
        total_votes = len(votes)
        winner = max(counts.keys(), key=lambda x: counts[x])
        
        return {
            "winner": winner,
            "counts": dict(counts),
            "percentage": counts[winner] / total_votes * 100,
            "method": "majority"
        }
    
    def weighted_vote(self, options: List[str], votes: Dict[str, str], weights: Dict[str, float]):
        """Vote pondéré par expertise"""
        if not weights:
            return self.majority_vote(options, votes)
        
        scores = defaultdict(float)
        
        for voter, choice in votes.items():
            weight = weights.get(voter, 1.0)
            if choice in options:
                scores[choice] += weight
        
        total_weight = sum(weights.values())
        winner = max(scores.keys(), key=lambda x: scores[x])
        
        return {
            "winner": winner,
            "scores": dict(scores),
            "percentage": scores[winner] / total_weight * 100,
            "method": "weighted"
        }
    
    def consensus_vote(self, options: List[str], votes: Dict[str, Dict[str, float]], weights=None):
        """Vote par score de consensus"""
        consensus_threshold = 0.7
        
        option_scores = defaultdict(list)
        
        # Collecter tous les scores
        for voter, scores in votes.items():
            for option, score in scores.items():
                if option in options:
                    option_scores[option].append(score)
        
        # Calculer consensus
        consensus_results = {}
        for option, scores in option_scores.items():
            avg_score = sum(scores) / len(scores)
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            consensus = 1 - (variance ** 0.5)  # Plus la variance est faible, plus le consensus est fort
            
            consensus_results[option] = {
                "average_score": avg_score,
                "consensus_level": consensus,
                "is_consensus": consensus >= consensus_threshold
            }
        
        # Trouver option avec meilleur consensus
        best_option = max(consensus_results.keys(), 
                         key=lambda x: consensus_results[x]["average_score"] * consensus_results[x]["consensus_level"])
        
        return {
            "winner": best_option if consensus_results[best_option]["is_consensus"] else None,
            "results": consensus_results,
            "method": "consensus"
        }
```

### Jour 4 : Agent Participant au Débat
**Fichier : agents/mixins/debater.py**
```python
class DebaterMixin:
    """Mixin pour donner capacité de débat à n'importe quel agent"""
    
    def __init__(self):
        self.debate_prompt_template = """
Tu participes à un débat sur : {topic}
Question : {question}

Ton rôle : {role}
Ta personnalité : {personality}

Arguments des autres participants :
{other_arguments}

Formule ton argument en tenant compte :
1. De ta perspective unique
2. Des arguments déjà présentés
3. Des faits et de la logique
4. De la recherche de solution

Réponds en JSON :
{{
    "position": "pour|contre|nuancé",
    "argument_principal": "ton argument clé",
    "raisonnement": "explication détaillée",
    "evidence": ["fait1", "fait2"],
    "réponse_aux_autres": {{"participant": "contre-argument"}}
}}
"""
    
    def participate_in_debate(self, debate_context: Dict[str, Any]) -> Argument:
        # Préparer contexte
        other_args = self._summarize_other_arguments(debate_context["arguments"])
        
        prompt = self.debate_prompt_template.format(
            topic=debate_context["topic"],
            question=debate_context["question"],
            role=self.role,
            personality=getattr(self, 'personality', 'neutral'),
            other_arguments=other_args
        )
        
        # Générer argument
        response = ollama.generate(
            model="llama3.2",
            prompt=prompt,
            format="json"
        )
        
        arg_data = json.loads(response['response'])
        
        return Argument(
            position=arg_data["position"],
            reasoning=arg_data["argument_principal"] + "\n\n" + arg_data["raisonnement"],
            evidence=arg_data["evidence"]
        )
    
    def vote_on_arguments(self, arguments: List[Argument]) -> Dict[str, float]:
        """Évalue et vote sur les arguments"""
        scores = {}
        
        for i, arg in enumerate(arguments):
            score = self._evaluate_argument(arg)
            scores[f"arg_{i}"] = score
        
        return scores
    
    def _evaluate_argument(self, argument: Argument) -> float:
        """Évalue un argument sur plusieurs critères"""
        criteria = {
            "logique": self._evaluate_logic(argument),
            "evidence": len(argument.evidence) / 5,  # Max 5 evidences
            "clarté": self._evaluate_clarity(argument),
            "pertinence": self._evaluate_relevance(argument)
        }
        
        # Moyenne pondérée
        weights = {"logique": 0.4, "evidence": 0.3, "clarté": 0.2, "pertinence": 0.1}
        
        score = sum(criteria[c] * weights[c] for c in criteria)
        return min(1.0, max(0.0, score))
```

### Jour 5 : Tests Débats
**Fichier : tests/test_debate.py**
```python
def test_debate_creation():
    moderator = DebateModerator()
    
    debate_id = moderator.create_debate(
        topic="Architecture logicielle",
        question="Microservices vs Monolithe pour ALMAA?",
        participants=["Architecte1", "Architecte2", "Dev1"]
    )
    
    assert debate_id in moderator.active_debates
    debate = moderator.active_debates[debate_id]
    assert len(debate.participants) == 3
    assert debate.status == "open"

def test_debate_round():
    # Setup
    bus = MessageBus()
    moderator = DebateModerator()
    
    # Créer agents avec capacité débat
    class TestDebater(BaseAgent, DebaterMixin):
        def __init__(self, name):
            BaseAgent.__init__(self, name, "Debater")
            DebaterMixin.__init__(self)
    
    agent1 = TestDebater("Agent1")
    agent2 = TestDebater("Agent2")
    
    bus.register_agent(moderator)
    bus.register_agent(agent1)
    bus.register_agent(agent2)
    
    # Créer débat
    debate_id = moderator.create_debate(
        "Test", "Question test?", ["Agent1", "Agent2"]
    )
    
    # Démarrer round
    moderator.start_round(debate_id)
    bus.process_messages()
    
    # Vérifier que les agents ont reçu l'invitation
    assert any(m.type == "REQUEST_ARGUMENT" for m in bus.message_history)

def test_voting_system():
    voting = VotingSystem()
    
    # Test vote majoritaire
    votes = {
        "Agent1": "OptionA",
        "Agent2": "OptionA", 
        "Agent3": "OptionB"
    }
    
    result = voting.conduct_vote(["OptionA", "OptionB"], votes, "majority")
    assert result["winner"] == "OptionA"
    assert result["percentage"] == pytest.approx(66.67, 0.01)
    
    # Test vote pondéré
    weights = {"Agent1": 2.0, "Agent2": 1.0, "Agent3": 1.0}
    result = voting.conduct_vote(["OptionA", "OptionB"], votes, "weighted", weights)
    assert result["winner"] == "OptionA"
    assert result["scores"]["OptionA"] == 3.0
```

## Semaine 6 : Système de Débats - Partie 2

### Jour 1-2 : Intégration Complète
**Fichier : core/debate_manager.py**
```python
class DebateManager:
    def __init__(self, message_bus: MessageBus):
        self.bus = message_bus
        self.moderator = DebateModerator()
        self.voting_system = VotingSystem()
        self.active_debates = {}
        
        # Enregistrer moderateur
        self.bus.register_agent(self.moderator)
    
    def initiate_debate(self, topic: str, question: str, 
                       participant_types: List[str]) -> str:
        """Initie un débat complet"""
        
        # Sélectionner participants
        participants = self._select_participants(participant_types)
        
        # Créer débat
        debate_id = self.moderator.create_debate(topic, question, participants)
        
        # Configurer suivi
        self.active_debates[debate_id] = {
            "start_time": datetime.now(),
            "rounds_completed": 0,
            "max_rounds": 3
        }
        
        # Démarrer premier round
        self.moderator.start_round(debate_id)
        
        return debate_id
    
    def _select_participants(self, types: List[str]) -> List[str]:
        """Sélectionne agents appropriés pour le débat"""
        available_agents = []
        
        for agent_name, agent in self.bus.agents.items():
            if hasattr(agent, 'participate_in_debate'):  # A la capacité de débattre
                if not types or any(t in agent.role for t in types):
                    available_agents.append(agent_name)
        
        # Limiter à 5 participants max
        return available_agents[:5]
    
    def process_debate_round(self, debate_id: str):
        """Traite un round de débat"""
        debate = self.moderator.active_debates.get(debate_id)
        if not debate:
            return
        
        # Collecter arguments
        current_round = debate.rounds[-1]
        
        # Vérifier si tous ont répondu
        all_responded = all(
            len(args) > 0 for args in current_round.arguments.values()
        )
        
        if all_responded:
            # Analyser round
            analysis = self._analyze_round(current_round)
            
            # Décider prochaine action
            if self.active_debates[debate_id]["rounds_completed"] >= self.active_debates[debate_id]["max_rounds"]:
                self._conclude_debate(debate_id)
            else:
                # Continuer avec nouveau round
                self.moderator.start_round(debate_id)
                self.active_debates[debate_id]["rounds_completed"] += 1
    
    def _conclude_debate(self, debate_id: str):
        """Conclut un débat avec vote final"""
        debate = self.moderator.active_debates[debate_id]
        
        # Collecter tous les arguments
        all_arguments = []
        for round in debate.rounds:
            for participant, args in round.arguments.items():
                all_arguments.extend(args)
        
        # Demander vote à tous les participants
        for participant in debate.participants:
            self.bus.publish(Message(
                sender=self.moderator.name,
                recipient=participant,
                type="REQUEST_VOTE",
                content={
                    "debate_id": debate_id,
                    "arguments": [arg.__dict__ for arg in all_arguments],
                    "options": self._extract_positions(all_arguments)
                }
            ))
```

### Jour 3 : Amélioration Agents avec Débat
**Fichier : agents/enhanced_chef.py**
```python
class EnhancedAgentChef(AgentChef, DebaterMixin):
    def __init__(self):
        AgentChef.__init__(self)
        DebaterMixin.__init__(self)
        self.personality = "strategic_visionary"
        self.debate_manager = None
    
    def process_message(self, message: Message) -> Optional[Message]:
        # Traiter messages de débat
        if message.type == "DEBATE_INVITATION":
            return self._handle_debate_invitation(message)
        elif message.type == "REQUEST_ARGUMENT":
            return self._provide_argument(message)
        elif message.type == "REQUEST_VOTE":
            return self._cast_vote(message)
        
        # Sinon, traitement normal
        return super().process_message(message)
    
    def _should_initiate_debate(self, analysis: Dict[str, Any]) -> bool:
        """Détermine si une décision nécessite un débat"""
        complexity = analysis.get("complexité", "simple")
        stakes = analysis.get("enjeux", "faibles")
        
        return complexity in ["moyenne", "complexe"] or stakes == "élevés"
    
    def _handle_user_request(self, message: Message) -> Message:
        # Analyser d'abord
        analysis = self.think({
            "user_request": message.content.get("request", "")
        })
        
        # Si complexe, initier débat
        if self._should_initiate_debate(analysis):
            debate_id = self.debate_manager.initiate_debate(
                topic=analysis["compréhension"],
                question=f"Quelle est la meilleure approche pour : {message.content['request']}?",
                participant_types=["Manager", "Expert", "Analyst"]
            )
            
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="RESPONSE",
                content={
                    "status": "debate_initiated",
                    "debate_id": debate_id,
                    "message": "J'ai initié un débat entre experts pour cette question complexe."
                }
            )
        else:
            # Traitement normal
            return super()._handle_user_request(message)
```

### Jour 4-5 : Documentation et Tests
**Fichier : docs/week5-6-debate-system.md**
```markdown
# Système de Débats - Documentation

## Architecture

### Composants Principaux
1. **Debate** : Structure de données pour un débat
2. **DebateModerator** : Agent qui modère les débats
3. **DebaterMixin** : Capacité de débat pour tout agent
4. **VotingSystem** : Mécaniques de vote variées
5. **DebateManager** : Orchestration haut niveau

### Flow d'un Débat
1. Chef identifie besoin de débat
2. DebateManager sélectionne participants
3. Moderator lance rounds
4. Agents soumettent arguments
5. Analyse et synthèse
6. Vote final
7. Implémentation décision

### Types de Votes
- **Majoritaire** : Simple majorité
- **Pondéré** : Par expertise
- **Consensus** : Accord général
- **Ranked Choice** : Préférences classées

## Exemples d'Usage

### Débat Simple
```python
# Initier débat
debate_id = debate_manager.initiate_debate(
    topic="Choix d'architecture",
    question="REST API ou GraphQL?",
    participant_types=["Architecte", "Développeur"]
)

# Processus automatique
while debate_active:
    bus.process_messages()
    debate_manager.process_debate_round(debate_id)
```

### Personnalisation
```python
# Agent avec opinion forte
class OpinionatedAgent(BaseAgent, DebaterMixin):
    def __init__(self):
        super().__init__("Opinionated", "Expert")
        self.personality = "contrarian"
        self.debate_style = "challenging"
```

## Tests
- ✅ Création débat
- ✅ Rounds multiples  
- ✅ Systèmes de vote
- ✅ Intégration agents
- ✅ Gestion timeouts

## Performance
- Débat 3 rounds : ~15 secondes
- 5 participants max recommandé
- Tokens : ~2000 par débat complet
```

## Semaine 7 : Mémoire Vectorielle - Partie 1

### Jour 1 : Setup ChromaDB
**Fichier : core/memory/vector_store.py**
```python
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import numpy as np

class VectorMemory:
    def __init__(self, persist_dir: str = "./data/memory/vectors"):
        # ChromaDB setup
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir
        ))
        
        # Modèle d'embedding
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collections
        self.collections = {
            "experiences": self.client.get_or_create_collection("experiences"),
            "knowledge": self.client.get_or_create_collection("knowledge"),
            "conversations": self.client.get_or_create_collection("conversations"),
            "decisions": self.client.get_or_create_collection("decisions")
        }
        
        # Config
        self.max_results = 10
        self.similarity_threshold = 0.7
    
    def store(self, content: str, metadata: Dict[str, Any], 
              collection_name: str = "experiences") -> str:
        """Stocke une information en mémoire"""
        
        # Générer embedding
        embedding = self.encoder.encode(content).tolist()
        
        # Créer ID unique
        doc_id = f"{collection_name}_{int(time.time() * 1000)}"
        
        # Ajouter metadata système
        metadata.update({
            "timestamp": datetime.now().isoformat(),
            "length": len(content),
            "collection": collection_name
        })
        
        # Stocker
        collection = self.collections[collection_name]
        collection.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        logger.debug(f"Stored in {collection_name}: {doc_id}")
        return doc_id
    
    def search(self, query: str, collection_name: Optional[str] = None,
               filters: Optional[Dict[str, Any]] = None,
               top_k: int = 5) -> List[Dict[str, Any]]:
        """Recherche sémantique dans la mémoire"""
        
        # Embedding de la requête
        query_embedding = self.encoder.encode(query).tolist()
        
        # Rechercher dans collection(s)
        if collection_name:
            collections = [self.collections[collection_name]]
        else:
            collections = self.collections.values()
        
        all_results = []
        
        for collection in collections:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            # Formatter résultats
            for i in range(len(results['ids'][0])):
                all_results.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i],
                    "similarity": 1 - results['distances'][0][i]
                })
        
        # Trier par similarité
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Filtrer par seuil
        filtered = [r for r in all_results if r['similarity'] >= self.similarity_threshold]
        
        return filtered[:self.max_results]
    
    def update(self, doc_id: str, content: Optional[str] = None,
               metadata_update: Optional[Dict[str, Any]] = None):
        """Met à jour un document existant"""
        
        # Trouver collection
        collection_name = doc_id.split('_')[0]
        collection = self.collections.get(collection_name)
        
        if not collection:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        # Récupérer document actuel
        current = collection.get(ids=[doc_id])
        
        if not current['ids']:
            raise ValueError(f"Document not found: {doc_id}")
        
        # Préparer updates
        new_content = content or current['documents'][0]
        new_metadata = current['metadatas'][0]
        
        if metadata_update:
            new_metadata.update(metadata_update)
        
        new_metadata['last_updated'] = datetime.now().isoformat()
        
        # Nouvel embedding si contenu changé
        if content:
            new_embedding = self.encoder.encode(new_content).tolist()
        else:
            new_embedding = None
        
        # Update
        collection.update(
            ids=[doc_id],
            documents=[new_content],
            metadatas=[new_metadata],
            embeddings=[new_embedding] if new_embedding else None
        )
    
    def forget(self, criteria: Dict[str, Any]):
        """Oubli sélectif selon critères"""
        
        to_delete = []
        
        # Chercher documents à oublier
        for collection_name, collection in self.collections.items():
            all_docs = collection.get()
            
            for i, metadata in enumerate(all_docs['metadatas']):
                doc_id = all_docs['ids'][i]
                
                # Vérifier critères
                if self._matches_criteria(metadata, criteria):
                    to_delete.append((collection_name, doc_id))
        
        # Supprimer
        deleted_count = 0
        for collection_name, doc_id in to_delete:
            self.collections[collection_name].delete(ids=[doc_id])
            deleted_count += 1
        
        logger.info(f"Forgot {deleted_count} memories matching criteria")
        return deleted_count
    
    def _matches_criteria(self, metadata: Dict[str, Any], 
                         criteria: Dict[str, Any]) -> bool:
        """Vérifie si metadata correspond aux critères"""
        
        for key, value in criteria.items():
            if key == "older_than":
                # Age en jours
                doc_time = datetime.fromisoformat(metadata.get('timestamp', ''))
                age = (datetime.now() - doc_time).days
                if age < value:
                    return False
            
            elif key == "importance_below":
                if metadata.get('importance', 1.0) >= value:
                    return False
            
            elif key in metadata:
                if metadata[key] != value:
                    return False
        
        return True
```

### Jour 2 : Intégration Mémoire aux Agents
**Fichier : agents/mixins/memory.py**
```python
class MemoryMixin:
    """Donne capacité de mémoire à un agent"""
    
    def __init__(self, memory_store: VectorMemory):
        self.memory = memory_store
        self.memory_config = {
            "auto_store": True,
            "importance_threshold": 0.5,
            "search_on_task": True
        }
    
    def remember_experience(self, content: str, metadata: Dict[str, Any]):
        """Stocke une expérience en mémoire"""
        
        # Calculer importance
        importance = self._calculate_importance(content, metadata)
        metadata['importance'] = importance
        metadata['agent'] = self.name
        
        # Stocker si assez important
        if importance >= self.memory_config['importance_threshold']:
            doc_id = self.memory.store(
                content=content,
                metadata=metadata,
                collection_name="experiences"
            )
            logger.debug(f"{self.name} remembered: {doc_id}")
            return doc_id
        
        return None
    
    def recall_similar(self, query: str, context: Optional[Dict] = None) -> List[Dict]:
        """Rappelle expériences similaires"""
        
        # Enrichir requête avec contexte
        if context:
            enriched_query = f"{query} Context: {str(context)}"
        else:
            enriched_query = query
        
        # Rechercher
        results = self.memory.search(
            query=enriched_query,
            filters={"agent": self.name} if self.memory_config.get('personal_only') else None,
            top_k=5
        )
        
        return results
    
    def learn_from_result(self, task: str, result: Any, success: bool):
        """Apprend d'un résultat"""
        
        content = f"""
Task: {task}
Result: {str(result)[:500]}
Success: {success}
Learning: {self._extract_learning(task, result, success)}
"""
        
        metadata = {
            "type": "task_result",
            "success": success,
            "task_type": self._classify_task(task)
        }
        
        self.remember_experience(content, metadata)
    
    def _calculate_importance(self, content: str, metadata: Dict[str, Any]) -> float:
        """Calcule l'importance d'une information"""
        
        factors = {
            "uniqueness": self._calculate_uniqueness(content),
            "success": 1.0 if metadata.get('success', False) else 0.3,
            "complexity": min(len(content) / 1000, 1.0),
            "recency": 1.0  # Décroîtra avec le temps
        }
        
        # Moyenne pondérée
        weights = {"uniqueness": 0.4, "success": 0.3, "complexity": 0.2, "recency": 0.1}
        
        importance = sum(factors[f] * weights[f] for f in factors)
        return min(1.0, max(0.0, importance))
    
    def _calculate_uniqueness(self, content: str) -> float:
        """Calcule l'unicité par rapport à la mémoire existante"""
        
        # Rechercher contenu similaire
        similar = self.memory.search(content, top_k=3)
        
        if not similar:
            return 1.0
        
        # Plus c'est similaire à l'existant, moins c'est unique
        avg_similarity = sum(r['similarity'] for r in similar) / len(similar)
        uniqueness = 1.0 - avg_similarity
        
        return max(0.0, uniqueness)
```

### Jour 3 : Agent avec Mémoire Complète
**Fichier : agents/memory_enhanced_worker.py**
```python
class MemoryEnhancedWorker(BaseAgent, DebaterMixin, MemoryMixin):
    def __init__(self, name: str, specialty: str, memory_store: VectorMemory):
        BaseAgent.__init__(self, name, f"Worker_{specialty}")
        DebaterMixin.__init__(self)
        MemoryMixin.__init__(self, memory_store)
        
        self.specialty = specialty
        self.completed_tasks = 0
        self.success_rate = 1.0
    
    def process_message(self, message: Message) -> Optional[Message]:
        # Chercher expériences pertinentes
        if self.memory_config['search_on_task'] and message.type in ["TASK_ASSIGNMENT", "CODE_TASK"]:
            similar_experiences = self.recall_similar(
                message.content.get('task', ''),
                context={"type": message.type}
            )
            
            if similar_experiences:
                logger.info(f"{self.name} found {len(similar_experiences)} similar experiences")
        
        # Traiter message
        response = super().process_message(message)
        
        # Mémoriser si pertinent
        if response and self.memory_config['auto_store']:
            self.remember_experience(
                content=f"Task: {message.content}\nResponse: {response.content}",
                metadata={
                    "message_type": message.type,
                    "success": True,
                    "task_type": self.specialty
                }
            )
        
        return response
    
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Penser avec aide de la mémoire"""
        
        # Rappeler expériences similaires
        task = context.get('task', '')
        memories = self.recall_similar(task)
        
        # Enrichir contexte avec souvenirs
        if memories:
            context['similar_experiences'] = [
                {
                    "content": m['content'][:200],
                    "success": m['metadata'].get('success', False),
                    "similarity": m['similarity']
                }
                for m in memories[:3]
            ]
        
        # Prompt enrichi
        enhanced_prompt = f"""
Tu es {self.name}, spécialiste en {self.specialty}.

Tâche : {task}

Expériences similaires :
{self._format_memories(memories)}

En te basant sur tes expériences passées et tes connaissances, propose la meilleure solution.
"""
        
        response = ollama.generate(
            model="llama3.2",
            prompt=enhanced_prompt
        )
        
        return {"response": response['response'], "memories_used": len(memories)}
    
    def _format_memories(self, memories: List[Dict]) -> str:
        if not memories:
            return "Aucune expérience similaire trouvée."
        
        formatted = []
        for i, mem in enumerate(memories[:3], 1):
            formatted.append(f"""
{i}. Similarité: {mem['similarity']:.1%}
   Succès: {'✓' if mem['metadata'].get('success') else '✗'}
   Résumé: {mem['content'][:150]}...
""")
        
        return "\n".join(formatted)
```

### Jour 4 : Compression et Optimisation
**Fichier : core/memory/compression.py**
```python
from sklearn.cluster import DBSCAN
import numpy as np

class MemoryCompressor:
    def __init__(self, vector_memory: VectorMemory):
        self.memory = vector_memory
        self.compression_threshold = 0.85  # Similarité pour compression
    
    def compress_memories(self, collection_name: str = "experiences", 
                         target_reduction: float = 0.5):
        """Compresse les mémoires similaires"""
        
        # Récupérer toutes les mémoires
        collection = self.memory.collections[collection_name]
        all_docs = collection.get()
        
        if len(all_docs['ids']) < 10:
            logger.info("Not enough memories to compress")
            return 0
        
        # Extraire embeddings
        embeddings = np.array(all_docs['embeddings'])
        
        # Clustering DBSCAN
        clustering = DBSCAN(eps=1-self.compression_threshold, min_samples=2, metric='cosine')
        clusters = clustering.fit_predict(embeddings)
        
        # Compresser chaque cluster
        compressed_count = 0
        
        for cluster_id in set(clusters):
            if cluster_id == -1:  # Bruit, pas de cluster
                continue
            
            # Indices du cluster
            cluster_indices = np.where(clusters == cluster_id)[0]
            
            if len(cluster_indices) >= 2:
                # Compresser ce cluster
                compressed = self._compress_cluster(
                    [all_docs['documents'][i] for i in cluster_indices],
                    [all_docs['metadatas'][i] for i in cluster_indices],
                    [all_docs['ids'][i] for i in cluster_indices]
                )
                
                if compressed:
                    compressed_count += len(cluster_indices) - 1
        
        logger.info(f"Compressed {compressed_count} memories")
        return compressed_count
    
    def _compress_cluster(self, documents: List[str], 
                         metadatas: List[Dict], 
                         ids: List[str]) -> Optional[str]:
        """Compresse un cluster de documents similaires"""
        
        # Créer résumé du cluster
        summary_prompt = f"""
Voici {len(documents)} expériences similaires :

{chr(10).join(f'{i+1}. {doc[:200]}...' for i, doc in enumerate(documents))}

Crée un résumé concis qui capture l'essence commune et les variations importantes.
"""
        
        response = ollama.generate(
            model="llama3.2",
            prompt=summary_prompt
        )
        
        summary = response['response']
        
        # Metadata combinée
        combined_metadata = {
            "type": "compressed",
            "original_count": len(documents),
            "original_ids": ids,
            "compression_date": datetime.now().isoformat(),
            "importance": max(m.get('importance', 0.5) for m in metadatas),
            "time_range": (
                min(m.get('timestamp', '') for m in metadatas),
                max(m.get('timestamp', '') for m in metadatas)
            )
        }
        
        # Stocker résumé
        summary_id = self.memory.store(summary, combined_metadata)
        
        # Supprimer originaux
        for doc_id in ids:
            collection_name = doc_id.split('_')[0]
            self.memory.collections[collection_name].delete(ids=[doc_id])
        
        return summary_id
```

### Jour 5 : Tests et Documentation
**Fichier : tests/test_memory.py**
```python
def test_vector_memory_store_and_search():
    memory = VectorMemory(persist_dir="./test_memory")
    
    # Stocker
    doc_id = memory.store(
        "Python est un excellent langage pour l'IA",
        {"language": "python", "topic": "ai"}
    )
    
    assert doc_id is not None
    
    # Rechercher
    results = memory.search("intelligence artificielle Python")
    
    assert len(results) > 0
    assert results[0]['similarity'] > 0.5

def test_memory_mixin_integration():
    memory = VectorMemory(persist_dir="./test_memory")
    
    class TestAgent(BaseAgent, MemoryMixin):
        def __init__(self):
            BaseAgent.__init__(self, "TestAgent", "Tester")
            MemoryMixin.__init__(self, memory)
    
    agent = TestAgent()
    
    # Mémoriser expérience
    doc_id = agent.remember_experience(
        "Completed task successfully using strategy X",
        {"task_type": "coding", "success": True}
    )
    
    # Rappeler
    similar = agent.recall_similar("task with strategy")
    
    assert len(similar) > 0
    assert "strategy X" in similar[0]['content']

def test_memory_compression():
    memory = VectorMemory(persist_dir="./test_memory")
    compressor = MemoryCompressor(memory)
    
    # Ajouter mémoires similaires
    for i in range(10):
        memory.store(
            f"Résolution bug dans module X variante {i}",
            {"type": "bugfix", "module": "X"}
        )
    
    # Compresser
    compressed = compressor.compress_memories()
    
    assert compressed > 0
    
    # Vérifier reduction
    all_docs = memory.collections["experiences"].get()
    assert len(all_docs['ids']) < 10
```

## Semaine 8 : Finalisation Intelligence

### Jour 1-2 : Intégration Complète
**Fichier : main.py**
```python
#!/usr/bin/env python3
"""
ALMAA v2.0 - Point d'entrée principal
"""

import click
import asyncio
from pathlib import Path

from core.communication import MessageBus
from core.memory.vector_store import VectorMemory
from core.debate_manager import DebateManager
from agents.enhanced_chef import EnhancedAgentChef
from agents.memory_enhanced_worker import MemoryEnhancedWorker
from interfaces.cli import ALMAACli
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger()

class ALMAA:
    def __init__(self, config_path: str = "config/default.yaml"):
        self.config = Config(config_path)
        self.bus = MessageBus()
        self.memory = VectorMemory()
        self.debate_manager = DebateManager(self.bus)
        
        self.setup_agents()
        
    def setup_agents(self):
        """Configure tous les agents avec capacités complètes"""
        
        # Chef avec débat
        chef = EnhancedAgentChef()
        chef.debate_manager = self.debate_manager
        self.bus.register_agent(chef)
        
        # Workers avec mémoire
        for i in range(3):
            worker = MemoryEnhancedWorker(
                name=f"Worker{i+1}",
                specialty=["coding", "analysis", "research"][i],
                memory_store=self.memory
            )
            self.bus.register_agent(worker)
        
        logger.info(f"Initialized {len(self.bus.agents)} agents")
    
    def process_request(self, request: str) -> Dict[str, Any]:
        """Traite une requête utilisateur"""
        
        start_time = time.time()
        
        # Envoyer au Chef
        message = Message(
            sender="User",
            recipient="Chef",
            type="USER_REQUEST",
            content={"request": request}
        )
        
        self.bus.publish(message)
        
        # Traiter jusqu'à réponse
        response = None
        max_iterations = 100
        
        for _ in range(max_iterations):
            self.bus.process_messages()
            
            # Chercher réponse
            for msg in self.bus.message_history:
                if msg.type == "RESPONSE" and msg.recipient == "User":
                    response = msg
                    break
            
            if response:
                break
            
            time.sleep(0.1)
        
        # Stats
        end_time = time.time()
        
        return {
            "response": response.content if response else "Timeout",
            "time": end_time - start_time,
            "messages_exchanged": len(self.bus.message_history),
            "debates_held": len(self.debate_manager.active_debates)
        }

@click.group()
def cli():
    """ALMAA - Système Multi-Agents Autonome"""
    pass

@cli.command()
@click.option('--config', default="config/default.yaml", help='Fichier de configuration')
def interactive(config):
    """Lance le mode interactif"""
    almaa = ALMAA(config)
    
    click.echo("🤖 ALMAA v2.0 - Mode Interactif")
    click.echo("Tapez 'exit' pour quitter, '/help' pour l'aide")
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
            
            # Traiter requête
            with click.progressbar(length=100, label='Traitement') as bar:
                result = almaa.process_request(user_input)
                bar.update(100)
            
            # Afficher résultat
            click.echo(f"\n🤖 ALMAA: {result['response']}")
            click.echo(f"⏱️  Temps: {result['time']:.2f}s | 💬 Messages: {result['messages_exchanged']}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            click.echo(f"❌ Erreur: {str(e)}", err=True)
    
    click.echo("\n👋 Au revoir!")

@cli.command()
@click.option('--request', '-r', required=True, help='Requête à traiter')
@click.option('--config', default="config/default.yaml")
def process(request, config):
    """Traite une requête unique"""
    almaa = ALMAA(config)
    result = almaa.process_request(request)
    
    click.echo(f"Réponse: {result['response']}")
    click.echo(f"Temps: {result['time']:.2f}s")

@cli.command()
def test():
    """Lance les tests du système"""
    click.echo("🧪 Lancement des tests...")
    
    # Tests basiques
    tests = [
        ("Communication", test_communication),
        ("Débats", test_debates),
        ("Mémoire", test_memory),
        ("Intégration", test_integration)
    ]
    
    for name, test_func in tests:
        try:
            test_func()
            click.echo(f"✅ {name}")
        except Exception as e:
            click.echo(f"❌ {name}: {str(e)}")

def test_communication():
    bus = MessageBus()
    assert len(bus.agents) == 0
    
def test_debates():
    manager = DebateManager(MessageBus())
    assert manager.voting_system is not None
    
def test_memory():
    memory = VectorMemory()
    doc_id = memory.store("test", {})
    assert doc_id is not None
    
def test_integration():
    almaa = ALMAA()
    assert len(almaa.bus.agents) > 0

if __name__ == '__main__':
    cli()
```

### Jour 3-4 : Documentation Finale Phase 2
**Fichier : docs/phase2-complete.md**
```markdown
# Phase 2 Complète : Intelligence

## ✅ Objectifs Atteints

### Système de Débats
- **Architecture**
  - DebateModerator agent
  - DebaterMixin pour tous agents
  - VotingSystem multi-méthodes
  - DebateManager orchestration

- **Fonctionnalités**
  - Débats multi-rounds
  - Arguments structurés
  - Votes (majorité, pondéré, consensus)
  - Synthèse automatique

- **Intégration**
  - Chef initie débats si complexe
  - Agents participent naturellement
  - Décisions traçables

### Mémoire Vectorielle
- **Architecture**
  - ChromaDB pour stockage
  - SentenceTransformers embeddings
  - Collections thématiques
  - Compression intelligente

- **Fonctionnalités**
  - Stockage expériences
  - Recherche sémantique
  - Oubli sélectif
  - Apprentissage continu

- **Intégration**
  - MemoryMixin pour agents
  - Recherche avant action
  - Mémorisation résultats

## Exemples d'Usage

### Débat Complexe
```python
# Requête utilisateur
"Quelle architecture choisir pour un système de paiement haute disponibilité?"

# Système:
1. Chef analyse → complexité élevée
2. Initie débat avec architectes
3. 3 rounds d'arguments
4. Vote consensus
5. Implémentation décision
```

### Mémoire en Action
```python
# Requête utilisateur
"Optimise cette fonction Python"

# Worker:
1. Recherche optimisations similaires
2. Trouve 3 expériences pertinentes
3. Applique patterns appris
4. Mémorise nouveau résultat
```

## Métriques Phase 2
- **Code ajouté** : ~3,000 lignes
- **Tests** : ~500 lignes
- **Complexité** : Modérée
- **Performance** : 
  - Débat 3 rounds : 15s
  - Recherche mémoire : 200ms

## Défis Résolus
1. **Synchronisation débats** → Timeouts + rounds limités
2. **Explosion mémoire** → Compression automatique
3. **Pertinence recherche** → Seuil similarité

## Architecture Finale
```
User Request
    ↓
AgentChef (analyse)
    ↓
[Simple] → Direct Process
[Complexe] → Debate System
    ↓
Workers (avec mémoire)
    ↓
Response
```

## Prochaine Phase
Phase 3 : Actions Concrètes (Code, Recherche, Documents)
```

### Jour 5 : Préparation Phase 3
```python
# Nettoyer et optimiser
# Documenter API complète  
# Préparer structure actions
```

---

# SUIVI ET MÉTRIQUES CONTINUES

## Dashboard de Suivi
```python
# À exécuter chaque semaine
python scripts/weekly_metrics.py

# Output:
"""
ALMAA Development Metrics - Week 8
==================================
Lines of Code: 4,523 (+3,023)
Test Coverage: 82% (+12%)
Documentation: 423 lines (+223)

Features Completed:
✅ Basic Agents
✅ Message System  
✅ Debate System
✅ Vector Memory
⬜ Code Actions
⬜ Search Actions
⬜ System Actions

Performance:
- Response Time: 1.2s avg
- Memory Usage: 156 MB
- Token Usage: ~2000/request

Next Week: Start Phase 3 - Actions
"""
```

## Checklist Continue
- [ ] Code review hebdomadaire
- [ ] Tests ajoutés pour nouvelles features
- [ ] Documentation à jour
- [ ] Performance mesurée
- [ ] Refactoring si nécessaire

---

Cette roadmap détaillée fournit un guide étape par étape pour les 8 premières semaines. La suite (semaines 9-20) suivrait le même format détaillé pour les phases 3, 4 et 5.