# agents/special/model_selector.py
from core.base import BaseAgent, Message
from typing import Dict, List, Any, Optional
import psutil
import subprocess
from loguru import logger

class ModelSelector(BaseAgent):
    """Agent responsable de la sélection optimale des modèles"""
    
    def __init__(self):
        super().__init__("ModelSelector", "ModelOptimizer")
        
        # Configuration des modèles disponibles
        self.available_models = {
            "llama3.2:latest": {
                "size_gb": 2.0,
                "capabilities": ["basic", "lightweight"],
                "speed": "fast",
                "quality": "low",
                "best_for": ["simple_tasks", "quick_responses"]
            },
            "nous-hermes2-demone:latest": {
                "size_gb": 26.0,
                "capabilities": ["reasoning", "general", "high_quality"],
                "speed": "slow",
                "quality": "high",
                "best_for": ["complex_reasoning", "leadership", "analysis"]
            },
            "solar:10.7b": {
                "size_gb": 6.1,
                "capabilities": ["general", "reasoning", "planning"],
                "speed": "medium",
                "quality": "good",
                "best_for": ["project_management", "coordination"]
            },
            "deepseek-coder:6.7b": {
                "size_gb": 3.8,
                "capabilities": ["coding", "debugging", "technical"],
                "speed": "fast",
                "quality": "specialized",
                "best_for": ["code_generation", "code_analysis", "debugging"]
            },
            "codellama:7b-code": {
                "size_gb": 3.8,
                "capabilities": ["coding", "technical"],
                "speed": "fast", 
                "quality": "specialized",
                "best_for": ["code_generation", "code_completion"]
            },
            "nous-hermes2-mixtral:latest": {
                "size_gb": 26.0,
                "capabilities": ["reasoning", "analysis", "high_quality"],
                "speed": "very_slow",
                "quality": "excellent",
                "best_for": ["deep_analysis", "philosophy", "complex_decisions"]
            },
            "phi:latest": {
                "size_gb": 1.6,
                "capabilities": ["basic", "ultra_lightweight"],
                "speed": "very_fast",
                "quality": "minimal",
                "best_for": ["simple_queries", "edge_computing"]
            }
        }
        
        # Mappings par défaut agent->modèle
        self.default_assignments = {
            "Chef": "solar:10.7b",  # Changé de llama3.2
            "ChefProjet": "solar:10.7b",
            "Developer": "deepseek-coder:6.7b",
            "Philosophe": "nous-hermes2-mixtral:latest",
            "Analyst": "solar:10.7b",
            "Researcher": "solar:10.7b",
            "Worker": "llama3.2:latest"
        }
        
        # État actuel des assignations
        self.current_assignments = self.default_assignments.copy()
        
        # Métriques de performance
        self.performance_history = {}
        
    def process_message(self, message: Message) -> Optional[Message]:
        """Traite les messages entrants"""
        if message.type == "MODEL_REQUEST":
            return self.handle_model_request(message)
        elif message.type == "PERFORMANCE_REPORT":
            return self.handle_performance_report(message)
        elif message.type == "OPTIMIZE_MODELS":
            return self.optimize_all_models(message)
        return None
        
    def handle_model_request(self, message: Message) -> Message:
        """Sélectionne le meilleur modèle pour un agent"""
        agent_name = message.content.get("agent_name")
        task_type = message.content.get("task_type", "general")
        priority = message.content.get("priority", "balanced")
        
        # Obtenir les ressources système
        system_resources = self.get_system_resources()
        
        # Sélectionner le modèle optimal
        selected_model = self.select_optimal_model(
            agent_name, task_type, priority, system_resources
        )
        
        logger.info(f"Selected {selected_model} for {agent_name}")
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            type="MODEL_ASSIGNMENT",
            content={
                "agent_name": agent_name,
                "model": selected_model,
                "reason": self.get_selection_reason(agent_name, selected_model)
            }
        )
        
    def select_optimal_model(self, agent_name: str, task_type: str, 
                           priority: str, resources: Dict) -> str:
        """Sélectionne le modèle optimal basé sur plusieurs critères"""
        
        # Obtenir le type d'agent
        agent_type = self.get_agent_type(agent_name)
        
        # Filtrer les modèles par capacités
        suitable_models = []
        for model_name, model_info in self.available_models.items():
            # Vérifier la RAM disponible
            if model_info["size_gb"] > resources["available_ram_gb"] * 0.7:
                continue
                
            # Vérifier les capacités
            if task_type == "coding" and "coding" in model_info["capabilities"]:
                suitable_models.append((model_name, model_info))
            elif task_type == "reasoning" and "reasoning" in model_info["capabilities"]:
                suitable_models.append((model_name, model_info))
            elif task_type == "general" and "general" in model_info["capabilities"]:
                suitable_models.append((model_name, model_info))
                
        # Si aucun modèle spécialisé, prendre un général
        if not suitable_models:
            suitable_models = [(m, i) for m, i in self.available_models.items() 
                             if "general" in i["capabilities"]]
        
        # Trier par priorité
        if priority == "quality":
            suitable_models.sort(key=lambda x: 
                ["minimal", "low", "good", "specialized", "high", "excellent"]
                .index(x[1]["quality"]), reverse=True)
        elif priority == "speed":
            suitable_models.sort(key=lambda x: 
                ["very_slow", "slow", "medium", "fast", "very_fast"]
                .index(x[1]["speed"]), reverse=True)
        else:  # balanced
            # Score composite
            for model_name, model_info in suitable_models:
                quality_score = ["minimal", "low", "good", "specialized", "high", "excellent"].index(model_info["quality"])
                speed_score = ["very_slow", "slow", "medium", "fast", "very_fast"].index(model_info["speed"]) 
                model_info["balanced_score"] = quality_score * 0.6 + speed_score * 0.4
            suitable_models.sort(key=lambda x: x[1].get("balanced_score", 0), reverse=True)
            
        # Retourner le meilleur modèle
        if suitable_models:
            return suitable_models[0][0]
        else:
            return "llama3.2:latest"  # Fallback
            
    def get_system_resources(self) -> Dict[str, float]:
        """Obtient les ressources système disponibles"""
        memory = psutil.virtual_memory()
        return {
            "total_ram_gb": memory.total / (1024**3),
            "available_ram_gb": memory.available / (1024**3),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_count": psutil.cpu_count()
        }
        
    def get_agent_type(self, agent_name: str) -> str:
        """Détermine le type d'agent basé sur son nom"""
        if "Chef" in agent_name and "Projet" not in agent_name:
            return "Chef"
        elif "ChefProjet" in agent_name:
            return "ChefProjet"
        elif "Developer" in agent_name:
            return "Developer"
        elif "Philosophe" in agent_name:
            return "Philosophe"
        elif "Analyst" in agent_name:
            return "Analyst"
        else:
            return "Worker"
            
    def optimize_all_models(self, message: Message) -> Message:
        """Optimise toutes les assignations de modèles"""
        optimized_assignments = {}
        resources = self.get_system_resources()
        
        for agent_name, current_model in self.current_assignments.items():
            # Analyser les performances historiques
            if agent_name in self.performance_history:
                avg_performance = sum(self.performance_history[agent_name]) / len(self.performance_history[agent_name])
                if avg_performance < 0.5:  # Performance faible
                    # Chercher un meilleur modèle
                    task_type = "general"
                    if "Developer" in agent_name:
                        task_type = "coding"
                    elif agent_name in ["Chef", "Philosophe"]:
                        task_type = "reasoning"
                        
                    new_model = self.select_optimal_model(
                        agent_name, task_type, "quality", resources
                    )
                    optimized_assignments[agent_name] = new_model
                else:
                    optimized_assignments[agent_name] = current_model
            else:
                optimized_assignments[agent_name] = current_model
                
        self.current_assignments = optimized_assignments
        
        return Message(
            sender=self.name,
            recipient=message.sender,
            type="OPTIMIZATION_COMPLETE",
            content={
                "assignments": optimized_assignments,
                "changes": self.get_assignment_changes(self.default_assignments, optimized_assignments)
            }
        )
        
    def handle_performance_report(self, message: Message) -> Optional[Message]:
        """Enregistre les rapports de performance"""
        agent_name = message.content.get("agent_name")
        performance_score = message.content.get("score", 0.5)
        
        if agent_name not in self.performance_history:
            self.performance_history[agent_name] = []
            
        self.performance_history[agent_name].append(performance_score)
        
        # Garder seulement les 10 derniers scores
        if len(self.performance_history[agent_name]) > 10:
            self.performance_history[agent_name] = self.performance_history[agent_name][-10:]
            
        return None
        
    def get_selection_reason(self, agent_name: str, model: str) -> str:
        """Explique pourquoi un modèle a été sélectionné"""
        model_info = self.available_models.get(model, {})
        agent_type = self.get_agent_type(agent_name)
        
        reasons = []
        if agent_type in model_info.get("best_for", []):
            reasons.append(f"Optimisé pour {agent_type}")
        if "capabilities" in model_info:
            reasons.append(f"Capacités: {', '.join(model_info['capabilities'])}")
        reasons.append(f"Qualité: {model_info.get('quality', 'unknown')}")
        reasons.append(f"Vitesse: {model_info.get('speed', 'unknown')}")
        
        return " | ".join(reasons)
        
    def get_assignment_changes(self, old: Dict, new: Dict) -> List[str]:
        """Compare les anciennes et nouvelles assignations"""
        changes = []
        for agent, new_model in new.items():
            old_model = old.get(agent)
            if old_model != new_model:
                changes.append(f"{agent}: {old_model} → {new_model}")
        return changes


# Intégration dans main.py
def integrate_model_selector():
    """
    Ajouter dans main.py après _setup_core_agents():
    """
    # Dans _setup_core_agents()
    model_selector = ModelSelector()
    self.register_agent(model_selector)
    
    # Demander l'optimisation des modèles au démarrage
    self.bus.publish(Message(
        sender="System",
        recipient="ModelSelector",
        type="OPTIMIZE_MODELS",
        content={}
    ))
    
    # Modifier les agents pour utiliser les modèles assignés
    def update_agent_models(assignments):
        for agent_name, model in assignments.items():
            if agent_name in self.agents:
                self.agents[agent_name].model = model
                logger.info(f"Updated {agent_name} to use {model}")
