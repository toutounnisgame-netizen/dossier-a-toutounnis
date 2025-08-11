"""
Tests complets pour le système de réponses ALMAA
Vérifie le bon fonctionnement du ResponseManager et du flux complet
"""
import pytest
import time
import threading
from datetime import datetime
from core.base import Message
from core.response_manager import ResponseManager, PendingRequest
from core.enhanced_messagebus import EnhancedMessageBus
from agents.user_response_collector import UserResponseCollector
from agents.simple_chef import SimpleChef


class TestResponseManager:
    """Tests pour le ResponseManager"""
    
    def test_create_request(self):
        """Test création de requête"""
        manager = ResponseManager()
        
        request_id = manager.create_request("Test request")
        
        assert request_id is not None
        assert request_id in manager.pending_requests
        assert manager.stats["requests_created"] == 1
        
    def test_register_and_get_response(self):
        """Test enregistrement et récupération de réponse"""
        manager = ResponseManager()
        
        # Créer requête
        request_id = manager.create_request("Test request")
        
        # Créer réponse
        response = Message(
            sender="Chef",
            recipient="User",
            type="RESPONSE",
            content={"message": "Test response"}
        )
        
        # Enregistrer réponse
        success = manager.register_response(response)
        assert success is True
        
        # Récupérer réponse
        result = manager.get_response(request_id, wait_timeout=1.0)
        
        assert result["success"] is True
        assert result["response"] == "Test response"
        assert "duration" in result
        
    def test_request_timeout(self):
        """Test timeout de requête"""
        manager = ResponseManager()
        
        # Créer requête avec timeout court
        request_id = manager.create_request("Test request", timeout=1)
        
        # Attendre expiration
        time.sleep(1.5)
        
        # Tenter de récupérer
        result = manager.get_response(request_id, wait_timeout=0.1)
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()
        
    def test_no_matching_request(self):
        """Test réponse sans requête correspondante"""
        manager = ResponseManager()
        
        # Envoyer réponse sans requête
        response = Message(
            sender="Chef",
            recipient="User", 
            type="RESPONSE",
            content={"message": "Orphan response"}
        )
        
        success = manager.register_response(response)
        assert success is False  # Aucune requête en attente
        
    def test_cleanup_expired_requests(self):
        """Test nettoyage automatique des requêtes expirées"""
        manager = ResponseManager()
        
        # Créer requête avec timeout très court
        request_id = manager.create_request("Test request", timeout=1)
        
        # Vérifier qu'elle existe
        assert request_id in manager.pending_requests
        
        # Attendre nettoyage automatique
        time.sleep(2)
        
        # Vérifier qu'elle a été nettoyée
        # Note: Le nettoyage se fait toutes les 5s, donc on force ici
        manager._cleanup_loop()
        assert request_id not in manager.pending_requests


class TestUserResponseCollector:
    """Tests pour UserResponseCollector"""
    
    def test_collect_response(self):
        """Test collecte de réponse"""
        response_manager = ResponseManager()
        collector = UserResponseCollector(response_manager)
        
        # Créer une réponse
        response = Message(
            sender="Chef",
            recipient="User",
            type="RESPONSE",
            content={"message": "Test response"}
        )
        
        # Traiter la réponse
        result = collector.process_message(response)
        
        # Vérifier collecte
        assert collector.responses_collected == 1
        assert len(collector.collected_responses) == 1
        assert collector.collected_responses[0] == response
        
    def test_handle_error(self):
        """Test gestion d'erreur"""
        response_manager = ResponseManager()
        collector = UserResponseCollector(response_manager)
        
        # Créer une erreur
        error = Message(
            sender="System",
            recipient="User",
            type="ERROR",
            content={"error": "Test error"}
        )
        
        # Traiter l'erreur
        collector.process_message(error)
        
        # Vérifier gestion
        assert collector.errors_handled == 1
        assert len(collector.collected_responses) == 1
        
    def test_get_stats(self):
        """Test statistiques"""
        response_manager = ResponseManager()
        collector = UserResponseCollector(response_manager)
        
        stats = collector.get_stats()
        
        assert "responses_collected" in stats
        assert "errors_handled" in stats
        assert "cached_responses" in stats
        assert "state" in stats


class TestEnhancedMessageBus:
    """Tests pour EnhancedMessageBus"""
    
    def test_routing_request(self):
        """Test routage des requêtes"""
        response_manager = ResponseManager()
        bus = EnhancedMessageBus(response_manager)
        bus.start()
        
        # Enregistrer agents
        chef = SimpleChef()
        collector = UserResponseCollector(response_manager)
        
        bus.register_agent(chef)
        bus.register_agent(collector)
        
        # S'abonner
        bus.subscribe("Chef", "REQUEST")
        bus.subscribe("User", "RESPONSE")
        
        # Publier requête
        request = Message(
            sender="User",
            type="REQUEST",
            content={"request": "Test request"}
        )
        
        bus.publish(request)
        
        # Attendre traitement
        time.sleep(0.2)
        bus.process_agent_messages()
        
        # Vérifier que Chef a reçu
        assert len(chef.inbox) > 0
        
        bus.stop()
        
    def test_agent_registration(self):
        """Test enregistrement d'agents"""
        bus = EnhancedMessageBus()
        
        chef = SimpleChef()
        bus.register_agent(chef)
        
        assert "Chef" in bus.agents
        assert bus.agents["Chef"] == chef
        
    def test_subscription(self):
        """Test abonnements"""
        bus = EnhancedMessageBus()
        
        bus.subscribe("Chef", "REQUEST")
        
        assert "Chef" in bus.subscribers["REQUEST"]
        
    def test_get_stats(self):
        """Test statistiques"""
        bus = EnhancedMessageBus()
        
        stats = bus.get_stats()
        
        assert "messages_sent" in stats
        assert "messages_delivered" in stats
        assert "messages_failed" in stats
        assert "agents_count" in stats


class TestCompleteFlow:
    """Tests du flux complet"""
    
    @pytest.fixture
    def setup_system(self):
        """Setup système complet pour tests"""
        response_manager = ResponseManager()
        bus = EnhancedMessageBus(response_manager)
        
        # Agents
        chef = SimpleChef()
        collector = UserResponseCollector(response_manager)
        
        bus.register_agent(chef)
        bus.register_agent(collector)
        
        # Subscriptions
        bus.subscribe("Chef", "REQUEST")
        bus.subscribe("User", "RESPONSE")
        
        bus.start()
        
        return {
            "response_manager": response_manager,
            "bus": bus,
            "chef": chef,
            "collector": collector
        }
        
    def test_complete_request_response_flow(self, setup_system):
        """Test du flux complet requête → réponse"""
        system = setup_system
        response_manager = system["response_manager"]
        bus = system["bus"]
        
        # Créer requête trackée
        request_id = response_manager.create_request("Test request")
        
        # Publier requête
        request = Message(
            sender="User",
            type="REQUEST",
            content={"request": "Test request", "request_id": request_id},
            thread_id=request_id
        )
        
        bus.publish(request)
        
        # Traitement
        max_iterations = 50
        for i in range(max_iterations):
            bus.process_agent_messages()
            
            result = response_manager.get_response(request_id, wait_timeout=0.1)
            
            if result["success"]:
                break
                
            time.sleep(0.1)
        
        # Vérifier réponse reçue
        assert result["success"] is True
        assert "response" in result
        
        bus.stop()
        response_manager.shutdown()
        
    def test_multiple_concurrent_requests(self, setup_system):
        """Test requêtes multiples concurrentes"""
        system = setup_system
        response_manager = system["response_manager"]
        bus = system["bus"]
        
        # Créer plusieurs requêtes
        request_ids = []
        for i in range(3):
            request_id = response_manager.create_request(f"Request {i}")
            request_ids.append(request_id)
            
            request = Message(
                sender="User",
                type="REQUEST", 
                content={"request": f"Request {i}", "request_id": request_id},
                thread_id=request_id
            )
            
            bus.publish(request)
        
        # Traitement
        results = []
        max_iterations = 100
        
        for i in range(max_iterations):
            bus.process_agent_messages()
            
            # Vérifier chaque requête
            for req_id in request_ids[:]:  # Copie pour modification
                result = response_manager.get_response(req_id, wait_timeout=0.1)
                
                if result["success"] or "error" in result:
                    results.append(result)
                    request_ids.remove(req_id)
            
            if not request_ids:  # Toutes traitées
                break
                
            time.sleep(0.1)
        
        # Vérifier que toutes ont été traitées
        assert len(results) == 3
        
        bus.stop()
        response_manager.shutdown()


def test_integration_with_mock_ollama():
    """Test d'intégration avec mock d'Ollama"""
    # Ce test nécessiterait un mock d'Ollama
    # À implémenter selon les besoins spécifiques
    pass


if __name__ == "__main__":
    # Lancer les tests
    pytest.main([__file__, "-v"])