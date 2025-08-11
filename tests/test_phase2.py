# -*- coding: utf-8 -*-
"""
Simple tests for ALMAA Phase 2
Basic unit tests for core functionality
"""

import pytest
from datetime import datetime
from core.base import Message, BaseAgent
from core.debate import Debate, Argument, DebateRound
from core.voting import VotingSystem
from core.memory.vector_store import VectorMemory
from agents.mixins.debater import DebaterMixin
from agents.mixins.memory import MemoryMixin


class TestDebateSystem:
    """Test debate functionality"""
    
    def test_create_debate(self):
        """Test debate creation"""
        debate = Debate("Architecture", "Microservices vs Monolith?")
        
        assert debate.topic == "Architecture"
        assert debate.question == "Microservices vs Monolith?"
        assert debate.status == "open"
        assert len(debate.participants) == 0
        
    def test_add_participants(self):
        """Test adding participants"""
        debate = Debate("Test", "Question?")
        
        debate.add_participant("Agent1")
        debate.add_participant("Agent2")
        
        assert len(debate.participants) == 2
        assert "Agent1" in debate.participants
        
    def test_start_round(self):
        """Test starting a debate round"""
        debate = Debate("Test", "Question?")
        debate.add_participant("Agent1")
        debate.add_participant("Agent2")
        
        round1 = debate.start_round()
        
        assert round1.number == 1
        assert round1.status == "open"
        assert len(round1.participants) == 2
        
    def test_add_argument(self):
        """Test adding arguments"""
        debate = Debate("Test", "Question?")
        debate.add_participant("Agent1")
        debate.add_participant("Agent2")
        
        round1 = debate.start_round()
        
        arg = Argument(
            position="pour",
            reasoning="Test reasoning",
            evidence=["fact1", "fact2"]
        )
        
        round1.add_argument("Agent1", arg)
        
        assert len(round1.arguments["Agent1"]) == 1
        assert round1.arguments["Agent1"][0].author == "Agent1"


class TestVotingSystem:
    """Test voting functionality"""
    
    def test_majority_vote(self):
        """Test simple majority voting"""
        voting = VotingSystem()
        
        votes = {
            "Agent1": "OptionA",
            "Agent2": "OptionA",
            "Agent3": "OptionB"
        }
        
        result = voting.conduct_vote(["OptionA", "OptionB"], votes, "majority")
        
        assert result["winner"] == "OptionA"
        assert result["percentage"] == pytest.approx(66.67, 0.01)
        
    def test_weighted_vote(self):
        """Test weighted voting"""
        voting = VotingSystem()
        
        votes = {
            "Expert": "OptionA",
            "Novice1": "OptionB",
            "Novice2": "OptionB"
        }
        
        weights = {
            "Expert": 3.0,
            "Novice1": 1.0,
            "Novice2": 1.0
        }
        
        result = voting.conduct_vote(
            ["OptionA", "OptionB"], 
            votes, 
            "weighted", 
            weights
        )
        
        assert result["winner"] == "OptionA"  # Expert's vote worth more
        
    def test_consensus_vote(self):
        """Test consensus voting"""
        voting = VotingSystem()
        
        votes = {
            "Agent1": {"OptionA": 0.9, "OptionB": 0.1},
            "Agent2": {"OptionA": 0.8, "OptionB": 0.2},
            "Agent3": {"OptionA": 0.85, "OptionB": 0.15}
        }
        
        result = voting.conduct_vote(["OptionA", "OptionB"], votes, "consensus")
        
        assert result["winner"] == "OptionA"
        assert result["results"]["OptionA"]["is_consensus"] == True


class TestMemorySystem:
    """Test memory functionality"""
    
    def test_store_and_retrieve(self, tmp_path):
        """Test storing and retrieving memories"""
        memory = VectorMemory(persist_dir=str(tmp_path))
        
        # Store a memory
        doc_id = memory.store(
            "Python is great for AI development",
            {"type": "knowledge", "importance": 0.8}
        )
        
        assert doc_id is not None
        
        # Search for it
        results = memory.search("Python programming")
        
        assert len(results) > 0
        assert results[0]["similarity"] > 0.5
        
    def test_memory_collections(self, tmp_path):
        """Test different memory collections"""
        memory = VectorMemory(persist_dir=str(tmp_path))
        
        # Store in different collections
        exp_id = memory.store("Task completed successfully", {}, "experiences")
        know_id = memory.store("Python fact", {}, "knowledge")
        
        # Get stats
        stats = memory.get_stats()
        
        assert stats["total_memories"] >= 2
        assert stats["collections"]["experiences"] >= 1
        assert stats["collections"]["knowledge"] >= 1
        
    def test_forgetting(self, tmp_path):
        """Test selective forgetting"""
        memory = VectorMemory(persist_dir=str(tmp_path))
        
        # Store memories with different importance
        memory.store("Important fact", {"importance": 0.9})
        memory.store("Trivial fact", {"importance": 0.2})
        
        # Forget unimportant memories
        forgotten = memory.forget({"importance_below": 0.5})
        
        assert forgotten >= 1


class TestDebaterMixin:
    """Test debater mixin functionality"""
    
    class TestAgent(BaseAgent, DebaterMixin):
        def __init__(self):
            BaseAgent.__init__(self, "TestAgent", "Tester")
            DebaterMixin.__init__(self)
            
    def test_participate_in_debate(self):
        """Test debate participation"""
        agent = self.TestAgent()
        
        # Mock debate context
        context = {
            "topic": "Test Topic",
            "question": "Test Question?",
            "arguments": []
        }
        
        # Generate argument
        argument = agent.participate_in_debate(context)
        
        assert isinstance(argument, Argument)
        assert argument.position in ["pour", "contre", "nuancé"]
        assert len(argument.reasoning) > 0
        
    def test_evaluate_argument(self):
        """Test argument evaluation"""
        agent = self.TestAgent()
        
        arg = Argument(
            position="pour",
            reasoning="Clear and logical reasoning with evidence",
            evidence=["fact1", "fact2", "fact3"]
        )
        
        score = agent.evaluate_argument(arg)
        
        assert 0 <= score <= 1
        assert score > 0.5  # Should be decent score


class TestMemoryMixin:
    """Test memory mixin functionality"""
    
    class TestAgent(BaseAgent, MemoryMixin):
        def __init__(self, memory_store):
            BaseAgent.__init__(self, "TestAgent", "Tester")
            MemoryMixin.__init__(self, memory_store)
            
    def test_remember_experience(self, tmp_path):
        """Test remembering experiences"""
        memory = VectorMemory(persist_dir=str(tmp_path))
        agent = self.TestAgent(memory)
        
        # Remember something
        doc_id = agent.remember_experience(
            "Completed task successfully",
            {"type": "test", "success": True}
        )
        
        assert doc_id is not None
        assert agent.memories_stored == 1
        
    def test_recall_similar(self, tmp_path):
        """Test recalling similar memories"""
        memory = VectorMemory(persist_dir=str(tmp_path))
        agent = self.TestAgent(memory)
        
        # Store some experiences
        agent.remember_experience(
            "Python function for fibonacci",
            {"type": "code", "success": True}
        )
        
        agent.remember_experience(
            "JavaScript async function",
            {"type": "code", "success": True}
        )
        
        # Recall similar
        memories = agent.recall_similar("fibonacci sequence")
        
        assert len(memories) > 0
        assert agent.memories_recalled > 0


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running ALMAA Phase 2 Tests...\n")
    
    # Test debate
    print("Testing Debate System...")
    debate_tests = TestDebateSystem()
    debate_tests.test_create_debate()
    debate_tests.test_add_participants()
    debate_tests.test_start_round()
    debate_tests.test_add_argument()
    print("✅ Debate tests passed")
    
    # Test voting
    print("\nTesting Voting System...")
    voting_tests = TestVotingSystem()
    voting_tests.test_majority_vote()
    voting_tests.test_weighted_vote()
    voting_tests.test_consensus_vote()
    print("✅ Voting tests passed")
    
    print("\n✅ All basic tests passed!")