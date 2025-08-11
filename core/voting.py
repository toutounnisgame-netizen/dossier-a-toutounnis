# -*- coding: utf-8 -*-
"""
Voting system for ALMAA v2.0
Multiple voting methods for debate conclusions
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict
from loguru import logger


class VotingSystem:
    """Handles different voting methods for debates"""
    
    def __init__(self):
        self.voting_methods = {
            "majority": self.majority_vote,
            "weighted": self.weighted_vote,
            "consensus": self.consensus_vote,
            "ranked": self.ranked_choice_vote
        }
        
    def conduct_vote(self, options: List[str], votes: Dict[str, Any], 
                    method: str = "majority", weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Conduct a vote using specified method"""
        if method not in self.voting_methods:
            raise ValueError(f"Unknown voting method: {method}")
            
        logger.info(f"Conducting {method} vote with {len(votes)} voters")
        
        if method == "weighted" and weights:
            return self.voting_methods[method](options, votes, weights)
        else:
            return self.voting_methods[method](options, votes)
            
    def majority_vote(self, options: List[str], votes: Dict[str, str]) -> Dict[str, Any]:
        """Simple majority vote"""
        counts = defaultdict(int)
        
        for voter, choice in votes.items():
            if choice in options:
                counts[choice] += 1
                
        total_votes = len(votes)
        if total_votes == 0:
            return {"winner": None, "counts": {}, "percentage": 0, "method": "majority"}
            
        winner = max(counts.keys(), key=lambda x: counts[x]) if counts else None
        percentage = (counts[winner] / total_votes * 100) if winner else 0
        
        return {
            "winner": winner,
            "counts": dict(counts),
            "percentage": percentage,
            "method": "majority"
        }
        
    def weighted_vote(self, options: List[str], votes: Dict[str, str], 
                     weights: Dict[str, float]) -> Dict[str, Any]:
        """Vote pondéré par expertise ou importance"""
        if not weights:
            return self.majority_vote(options, votes)
            
        scores = defaultdict(float)
        
        for voter, choice in votes.items():
            weight = weights.get(voter, 1.0)
            if choice in options:
                scores[choice] += weight
                
        total_weight = sum(weights.values())
        if total_weight == 0:
            return {"winner": None, "scores": {}, "percentage": 0, "method": "weighted"}
            
        winner = max(scores.keys(), key=lambda x: scores[x]) if scores else None
        percentage = (scores[winner] / total_weight * 100) if winner else 0
        
        return {
            "winner": winner,
            "scores": dict(scores),
            "percentage": percentage,
            "total_weight": total_weight,
            "method": "weighted"
        }
        
    def consensus_vote(self, options: List[str], votes: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Vote par score de consensus (chaque votant donne un score à chaque option)"""
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
            if not scores:
                continue
                
            avg_score = sum(scores) / len(scores)
            # Variance pour mesurer le consensus
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            # Plus la variance est faible, plus le consensus est fort
            consensus = 1 - (variance ** 0.5)  # Normaliser
            
            consensus_results[option] = {
                "average_score": avg_score,
                "consensus_level": consensus,
                "is_consensus": consensus >= consensus_threshold
            }
            
        # Trouver option avec meilleur consensus ET score
        best_option = None
        if consensus_results:
            # Prioriser consensus puis score moyen
            best_option = max(consensus_results.keys(), 
                            key=lambda x: (consensus_results[x]["consensus_level"],
                                         consensus_results[x]["average_score"]))
            
        return {
            "winner": best_option if consensus_results.get(best_option, {}).get("is_consensus") else None,
            "results": consensus_results,
            "method": "consensus",
            "threshold": consensus_threshold
        }
        
    def ranked_choice_vote(self, options: List[str], votes: Dict[str, List[str]]) -> Dict[str, Any]:
        """Vote par classement (instant runoff)"""
        candidates = set(options)
        round_number = 1
        elimination_rounds = []
        
        while len(candidates) > 1:
            # Compter les premiers choix
            first_choices = defaultdict(int)
            for voter, rankings in votes.items():
                # Trouver le premier choix encore en lice
                for choice in rankings:
                    if choice in candidates:
                        first_choices[choice] += 1
                        break
                        
            total_votes = sum(first_choices.values())
            if total_votes == 0:
                break
                
            # Vérifier si un candidat a la majorité
            for candidate, count in first_choices.items():
                if count > total_votes / 2:
                    return {
                        "winner": candidate,
                        "final_round": round_number,
                        "percentage": (count / total_votes * 100),
                        "elimination_rounds": elimination_rounds,
                        "method": "ranked"
                    }
                    
            # Éliminer le candidat avec le moins de votes
            if first_choices:
                eliminated = min(first_choices.keys(), key=lambda x: first_choices[x])
                candidates.remove(eliminated)
                elimination_rounds.append({
                    "round": round_number,
                    "eliminated": eliminated,
                    "votes": first_choices[eliminated]
                })
                round_number += 1
            else:
                break
                
        # S'il reste un candidat
        winner = list(candidates)[0] if len(candidates) == 1 else None
        
        return {
            "winner": winner,
            "final_round": round_number,
            "elimination_rounds": elimination_rounds,
            "method": "ranked"
        }