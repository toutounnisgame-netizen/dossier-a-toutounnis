# -*- coding: utf-8 -*-
"""
Chef de Projet Agent for ALMAA v2.0 - FIXED HANDLERS VERSION
Project planning and coordination with proper message handling
"""
from core.base import BaseAgent, Message
from agents.mixins.debater import DebaterMixin
from typing import Optional, Dict, Any, List
from core.ollama_client import generate  # Use fixed client
import json
from datetime import datetime, timedelta
from uuid import uuid4
from loguru import logger


class AgentChefProjet(BaseAgent, DebaterMixin):
    """Agent Chef de Projet - Planning and coordination with debate capability"""
    
    def __init__(self):
        BaseAgent.__init__(self, "ChefProjet", "CPO")
        DebaterMixin.__init__(self)
        
        self.active_projects = {}
        self.task_queue = []
        self.resource_allocation = {}
        self.model = "solar:10.7b"  # Better model for planning
        self.processed_messages = set()  # Prevent loops
        
        self.prompt_template = """
Tu es Chef de Projet dans une organisation d'agents IA.

Tâche reçue: {task}
Contexte: {context}
Ressources disponibles: {resources}

Ton rôle:
1. Analyser la complexité et les besoins de la tâche
2. La décomposer en sous-tâches atomiques si nécessaire
3. Créer un plan d'action séquentiel ou parallèle
4. Estimer le temps et les ressources nécessaires
5. Identifier les dépendances entre sous-tâches

Réponds en JSON:
{{
    "analyse": "description/analyse détaillée de la tâche",
    "complexité": 1-10,
    "type_principal": "code|analyse|recherche|création",
    "risques": ["risque1", "risque2"],
    "décomposition": [
        {{
            "id": "subtask1",
            "titre": "titre de la sous-tâche",
            "description": "description détaillée",
            "type": "code|analyse|recherche|test",
            "agent_type": "developer|analyst|researcher",
            "priorité": 1-10,
            "temps_estimé": "Xh",
            "dépendances": [],
            "critères_succès": ["critère1", "critère2"]
        }}
    ],
    "plan_exécution": {{
        "stratégie": "séquentiel|parallèle|hybride",
        "temps_total_estimé": "Xh",
        "jalons": [
            {{"nom": "jalon1", "date": "T+Xh", "livrables": ["livrable1"]}}
        ]
    }},
    "ressources_requises": {{
        "agents": ["type1", "type2"],
        "outils": ["outil1", "outil2"],
        "données": ["donnée1"]
    }}
}}
"""
        
        # Message handlers specific to ChefProjet
        self.message_handlers.update({
            "TASK_ASSIGNMENT": self.handle_task_assignment,
            "TASK_RESULT": self.handle_task_result,  # Add TASK_RESULT handler
            "SUBTASK_COMPLETE": self.handle_subtask_completion,
            "PROGRESS_REQUEST": self.handle_progress_request,
            "DEBATE_INVITATION": self.handle_debate_invitation,
            "REQUEST_ARGUMENT": self.handle_argument_request,
            "REQUEST_VOTE": self.handle_vote_request,
            "RESPONSE": self.handle_response,  # Add RESPONSE handler
            "ERROR": self.handle_error  # Add ERROR handler
        })
        
    def process_message(self, message: Message) -> Optional[Message]:
        """Process messages directed to ChefProjet - REQUIRED METHOD"""
        # Prevent message loops
        message_id = f"{message.sender}_{message.type}_{hash(str(message.content))}"
        if message_id in self.processed_messages:
            logger.debug(f"ChefProjet: Ignoring duplicate message {message_id}")
            return None
        self.processed_messages.add(message_id)
        
        # Clean old processed messages (keep last 100)
        if len(self.processed_messages) > 100:
            self.processed_messages.clear()
        
        handler = self.message_handlers.get(message.type)
        if handler:
            try:
                return handler(message)
            except Exception as e:
                logger.error(f"ChefProjet handler error for {message.type}: {e}")
                return Message(
                    sender=self.name,
                    recipient=message.sender,
                    type="ERROR",
                    content={"error": f"Handler error: {str(e)}"}
                )
        else:
            # Just log unknown types, don't send response to avoid loops
            logger.debug(f"ChefProjet: Unknown message type {message.type} from {message.sender}")
            return None
            
    def handle_response(self, message: Message) -> Optional[Message]:
        """Handle RESPONSE messages to prevent loops"""
        # Just log and ignore to prevent response loops
        logger.debug(f"ChefProjet received RESPONSE from {message.sender}")
        return None
        
    def handle_error(self, message: Message) -> Optional[Message]:
        """Handle ERROR messages"""
        error_content = message.content.get("error", "Unknown error")
        logger.error(f"ChefProjet received error from {message.sender}: {error_content}")
        return None  # Don't propagate errors to avoid loops
        
    def handle_task_result(self, message: Message) -> Optional[Message]:
        """Handle task completion results"""
        result = message.content
        
        # Send result back to original requester (usually Chef)
        original_sender = result.get("original_sender", "Chef")
        
        return Message(
            sender=self.name,
            recipient=original_sender,
            type="TASK_RESULT",
            content={
                "status": "completed",
                "original_sender": "User",  # Ultimate destination
                "result": result.get("result", "Tâche terminée"),
                "completed_by": message.sender,
                "project_completed": True
            }
        )
        
    def handle_task_assignment(self, message: Message) -> Optional[Message]:
        """Handle a new task assignment"""
        task_info = message.content
        logger.info(f"ChefProjet received task: {task_info.get('task', '')[:50]}...")
        
        # Create a new project
        project = self.create_project(task_info, message.sender)
        
        # Analyze and plan
        plan = self.think({
            "task": task_info.get("task", ""),
            "context": task_info.get("context", {}),
            "resources": self.get_available_resources()
        })
        
        if not plan:
            # Fallback for simple tasks
            return self.handle_simple_task(task_info, message.sender)
            
        # Save the plan
        project["plan"] = plan
        project["status"] = "planned"
        
        # If debate required, participate
        if task_info.get("require_debate", False):
            # Will participate through debate mixin
            return None
            
        # Otherwise, start execution
        return self.start_execution(project)
        
    def handle_simple_task(self, task_info: Dict[str, Any], sender: str) -> Message:
        """Handle simple task without complex planning"""
        task = task_info.get("task", "")
        
        # Simple delegation to Worker1
        return Message(
            sender=self.name,
            recipient="Worker1",
            type="TASK_ASSIGNMENT",
            content={
                "task": task,
                "original_sender": task_info.get("original_sender", "User"),
                "simple_task": True
            }
        )
        
    def create_project(self, task_info: Dict[str, Any], requester: str) -> Dict[str, Any]:
        """Create a new project"""
        project_id = f"proj_{int(datetime.now().timestamp())}"
        
        project = {
            "id": project_id,
            "task": task_info.get("task", ""),
            "context": task_info.get("context", {}),
            "requester": requester,
            "created_at": datetime.now(),
            "status": "created",
            "plan": None,
            "subtasks": {},
            "progress": 0,
            "results": {}
        }
        
        self.active_projects[project_id] = project
        logger.info(f"Created project {project_id}")
        
        return project
        
    def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a task with LLM"""
        try:
            prompt = self.prompt_template.format(
                task=context.get("task", ""),
                context=json.dumps(context.get("context", {}), ensure_ascii=False),
                resources=json.dumps(context.get("resources", {}), ensure_ascii=False)
            )
            
            response = generate(
                model=self.model,
                prompt=prompt,
                format="json",
                options={
                    "temperature": 0.7,
                    "num_predict": 2048
                }
            )
            
            plan = json.loads(response["response"])
            logger.debug(f"Generated plan with {len(plan.get('décomposition', []))} subtasks")
            return plan
            
        except Exception as e:
            logger.error(f"Planning error: {e}")
            return None
            
    def start_execution(self, project: Dict[str, Any]) -> Optional[Message]:
        """Start executing a project"""
        plan = project.get("plan", {})
        decomposition = plan.get("décomposition", [])
        
        if not decomposition:
            # Simple task, assign directly
            return self.assign_simple_task(project)
            
        # Identify tasks without dependencies
        ready_tasks = [
            task for task in decomposition 
            if not task.get("dépendances", [])
        ]
        
        if not ready_tasks:
            return self.report_error(
                project["requester"], 
                "Aucune tâche prête à démarrer"
            )
            
        # Assign first ready task
        first_task = ready_tasks[0]
        return self.assign_subtask(project, first_task)
        
    def assign_subtask(self, project: Dict[str, Any], subtask: Dict[str, Any]) -> Message:
        """Assign a subtask to an agent"""
        agent_type = subtask.get("agent_type", "developer")
        agent_name = self.find_available_agent(agent_type)
        
        if not agent_name:
            # Create worker name if none available
            agent_name = f"{agent_type.capitalize()}1"
            
        # Track assignment
        project["subtasks"][subtask["id"]] = {
            "assigned_to": agent_name,
            "status": "assigned",
            "started_at": datetime.now()
        }
        
        # Create assignment message
        return Message(
            sender=self.name,
            recipient=agent_name,
            type="TASK_ASSIGNMENT",
            content={
                "task": subtask["description"],
                "subtask_id": subtask["id"],
                "project_id": project["id"],
                "type": subtask["type"],
                "criteria": subtask.get("critères_succès", []),
                "deadline": self.calculate_deadline(subtask),
                "original_sender": "User"
            }
        )
        
    def handle_subtask_completion(self, message: Message) -> Optional[Message]:
        """Handle completion of a subtask"""
        result = message.content
        project_id = result.get("project_id")
        subtask_id = result.get("subtask_id")
        
        if not project_id or project_id not in self.active_projects:
            logger.error(f"Unknown project: {project_id}")
            return None
            
        project = self.active_projects[project_id]
        
        # Update status
        if subtask_id in project["subtasks"]:
            project["subtasks"][subtask_id]["status"] = "completed"
            project["subtasks"][subtask_id]["completed_at"] = datetime.now()
            
        project["results"][subtask_id] = result.get("result")
        
        # Calculate progress
        total_subtasks = len(project["plan"].get("décomposition", []))
        completed_subtasks = sum(
            1 for s in project["subtasks"].values() 
            if s["status"] == "completed"
        )
        project["progress"] = int(completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 100
        
        # Check if project is complete
        if project["progress"] >= 100:
            return self.complete_project(project)
            
        # Otherwise, assign next task
        next_task = self.get_next_task(project)
        if next_task:
            return self.assign_subtask(project, next_task)
            
        return None
        
    def get_next_task(self, project: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Identify the next task to execute"""
        plan = project.get("plan", {})
        decomposition = plan.get("décomposition", [])
        
        for task in decomposition:
            task_id = task["id"]
            
            # Skip if already assigned
            if task_id in project["subtasks"]:
                continue
                
            # Check dependencies
            dependencies = task.get("dépendances", [])
            dependencies_met = all(
                project["subtasks"].get(dep, {}).get("status") == "completed"
                for dep in dependencies
            )
            
            if dependencies_met:
                return task
                
        return None
        
    def complete_project(self, project: Dict[str, Any]) -> Message:
        """Complete a project and send results"""
        project["status"] = "completed"
        project["completed_at"] = datetime.now()
        
        # Compile final results
        final_result = {
            "project_id": project["id"],
            "task": project["task"],
            "status": "completed",
            "results": project["results"],
            "duration": str(project["completed_at"] - project["created_at"]),
            "progress": 100,
            "original_sender": "User"
        }
        
        # Send to original requester
        return Message(
            sender=self.name,
            recipient=project["requester"],
            type="TASK_RESULT",
            content=final_result
        )
        
    def calculate_deadline(self, subtask: Dict[str, Any]) -> Optional[str]:
        """Calculate deadline for a subtask"""
        time_estimate = subtask.get("temps_estimé", "1h")
        
        # Simple parsing (to be improved)
        hours = 1
        if "h" in time_estimate:
            try:
                hours = int(time_estimate.replace("h", ""))
            except:
                hours = 1
                
        deadline = datetime.now() + timedelta(hours=hours)
        return deadline.isoformat()
        
    def find_available_agent(self, agent_type: str) -> Optional[str]:
        """Find an available agent of the specified type"""
        # For now, return a default name (to be improved with real resource management)
        if agent_type == "developer":
            return "Worker1"
        elif agent_type == "analyst":
            return "Worker2"
        elif agent_type == "researcher":
            return "Worker3"
        else:
            return "Worker1"
        
    def get_available_resources(self) -> Dict[str, Any]:
        """Get available resources"""
        return {
            "agents": ["developer", "analyst", "researcher"],
            "tools": ["ollama", "python", "chromadb"],
            "memory": "vector_store_available"
        }
        
    def report_error(self, recipient: str, error: str) -> Message:
        """Report an error"""
        return Message(
            sender=self.name,
            recipient=recipient,
            type="ERROR",
            content={
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    def handle_progress_request(self, message: Message) -> Message:
        """Respond to progress request"""
        project_id = message.content.get("project_id")
        
        if project_id and project_id in self.active_projects:
            project = self.active_projects[project_id]
            
            return Message(
                sender=self.name,
                recipient=message.sender,
                type="PROGRESS_REPORT",
                content={
                    "project_id": project_id,
                    "progress": project["progress"],
                    "status": project["status"],
                    "subtasks": len(project["subtasks"]),
                    "completed": sum(
                        1 for s in project["subtasks"].values() 
                        if s["status"] == "completed"
                    )
                }
            )
            
        return self.report_error(message.sender, "Project not found")
        
    def assign_simple_task(self, project: Dict[str, Any]) -> Message:
        """Assign a simple task without decomposition"""
        # Find appropriate worker
        task_type = project["plan"].get("type_principal", "general") if project.get("plan") else "general"
        
        if task_type == "code":
            agent_name = "Worker1"
        elif task_type == "analyse":
            agent_name = "Worker2"
        else:
            agent_name = "Worker1"
            
        return Message(
            sender=self.name,
            recipient=agent_name,
            type="TASK_ASSIGNMENT",
            content={
                "task": project["task"],
                "project_id": project["id"],
                "type": task_type,
                "original_sender": "User"
            }
        )