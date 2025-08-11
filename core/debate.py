# -*- coding: utf-8 -*-
"""
Core debate system for ALMAA v2.0
Handles multi-agent debates with rounds, arguments, and voting
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4
from loguru import logger
from core.base import BaseAgent, Message


class Argument:
    """Represents a single argument in a debate"""
    
    def __init__(self, position: str, reasoning: str, evidence: List[str] = None):
        self.id = str(uuid4())
        self.position = position  # "pour", "contre", "nuancé"
        self.reasoning = reasoning
        self.evidence = evidence or []
        self.timestamp = datetime.now()
        self.votes = 0
        self.author = None  # Will be set by the agent
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "position": self.position,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "author": self.author,
            "votes": self.votes,
            "timestamp": self.timestamp.isoformat()
        }


class DebateRound:
    """Represents a single round in a debate"""
    
    def __init__(self, number: int, participants: List[str]):
        self.number = number
        self.participants = participants
        self.arguments: Dict[str, List[Argument]] = {p: [] for p in participants}
        self.status = "open"  # open, closed
        self.started_at = datetime.now()
        self.closed_at = None
        
    def add_argument(self, participant: str, argument: Argument):
        """Add an argument from a participant"""
        if participant in self.arguments:
            argument.author = participant
            self.arguments[participant].append(argument)
            logger.debug(f"{participant} added argument in round {self.number}")
            
    def close(self):
        """Close this round"""
        self.status = "closed"
        self.closed_at = datetime.now()
        logger.info(f"Round {self.number} closed")
        
    def get_all_arguments(self) -> List[Argument]:
        """Get all arguments from all participants"""
        all_args = []
        for args in self.arguments.values():
            all_args.extend(args)
        return all_args


class Debate:
    """Main debate class that manages the entire debate process"""
    
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
        self.closed_at = None
        
        # Configuration
        self.max_rounds = 3
        self.min_participants = 2
        self.max_participants = 7
        
        logger.info(f"Created debate {self.id[:8]} on topic: {topic}")
        
    def add_participant(self, agent_name: str):
        """Add a participant to the debate"""
        if agent_name not in self.participants and len(self.participants) < self.max_participants:
            self.participants.append(agent_name)
            logger.debug(f"{agent_name} joined debate {self.id[:8]}")
            
    def can_start(self) -> bool:
        """Check if debate can start"""
        return len(self.participants) >= self.min_participants
        
    def start_round(self) -> DebateRound:
        """Start a new round of debate"""
        if not self.can_start():
            raise ValueError("Not enough participants to start debate")
            
        round_num = len(self.rounds) + 1
        new_round = DebateRound(round_num, self.participants)
        self.rounds.append(new_round)
        self.status = "active"
        
        logger.info(f"Started round {round_num} of debate {self.id[:8]}")
        return new_round
        
    def close_current_round(self):
        """Close the current round"""
        if self.rounds:
            self.rounds[-1].close()
            
    def start_voting(self):
        """Move to voting phase"""
        self.status = "voting"
        logger.info(f"Debate {self.id[:8]} moved to voting phase")
        
    def conclude(self, result: Dict[str, Any]):
        """Conclude the debate with a result"""
        self.status = "closed"
        self.result = result
        self.closed_at = datetime.now()
        logger.info(f"Debate {self.id[:8]} concluded: {result.get('winner', 'No winner')}")
        
    def get_synthesis(self) -> Dict[str, Any]:
        """Generate a synthesis of the debate"""
        all_arguments = []
        for round in self.rounds:
            all_arguments.extend(round.get_all_arguments())
            
        # Group by position
        positions = {"pour": [], "contre": [], "nuancé": []}
        for arg in all_arguments:
            if arg.position in positions:
                positions[arg.position].append(arg)
                
        # Find consensus points
        consensus_points = []
        disagreement_points = []
        
        # Simple analysis (to be improved with LLM)
        if len(positions["pour"]) > 0 and len(positions["contre"]) == 0:
            consensus_points.append("Accord général sur la proposition")
        elif len(positions["contre"]) > 0 and len(positions["pour"]) == 0:
            consensus_points.append("Rejet général de la proposition")
        else:
            disagreement_points.append("Opinions divergentes sur la proposition")
            
        return {
            "total_arguments": len(all_arguments),
            "positions": {k: len(v) for k, v in positions.items()},
            "consensus_points": consensus_points,
            "disagreement_points": disagreement_points,
            "rounds_completed": len(self.rounds)
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert debate to dictionary"""
        return {
            "id": self.id,
            "topic": self.topic,
            "question": self.question,
            "participants": self.participants,
            "moderator": self.moderator,
            "status": self.status,
            "rounds": len(self.rounds),
            "created_at": self.created_at.isoformat(),
            "result": self.result
        }