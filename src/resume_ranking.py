"""
Simple candidate ranking implementation.

Provides CandidateRanker with a score_candidate(features, job_requirements)
method that returns a dict with 'total_score' and 'breakdown'.

This is intentionally lightweight and does not require heavy ML libs.
It uses skill overlap, token-based semantic similarity (Jaccard on tokens),
and experience matching as components.
"""
from typing import Dict, Any
import math
import re


class CandidateRanker:
    def __init__(self, skill_weight: float = 0.5, semantic_weight: float = 0.3, experience_weight: float = 0.2):
        # weights should sum to 1.0 (not strictly enforced)
        self.skill_weight = skill_weight
        self.semantic_weight = semantic_weight
        self.experience_weight = experience_weight

    def _token_set(self, text: str):
        if not text:
            return set()
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return set(tokens)

    def _skill_score(self, candidate_skills, required_skills):
        if not required_skills:
            return 1.0 if candidate_skills else 0.0
        req = {s.strip().lower() for s in required_skills if s}
        cand = {s.strip().lower() for s in candidate_skills if s}
        if not req:
            return 0.0
        matches = len(req & cand)
        return matches / len(req)

    def _semantic_score(self, candidate_text: str, job_description: str):
        if not candidate_text or not job_description:
            return 0.0
        a = self._token_set(candidate_text)
        b = self._token_set(job_description)
        if not a or not b:
            return 0.0
        inter = a & b
        union = a | b
        return len(inter) / len(union)

    def _experience_score(self, candidate_years, required_years):
        try:
            if required_years is None or required_years <= 0:
                return 1.0
            if candidate_years is None:
                return 0.0
            # if candidate has >= required, full score
            if candidate_years >= required_years:
                return 1.0
            # otherwise proportionally less
            return max(0.0, candidate_years / float(required_years))
        except Exception:
            return 0.0

    def score_candidate(self, features: Dict[str, Any], job_requirements: Dict[str, Any]):
        """
        Score a single candidate.

        features: output from NLPProcessor.extract_features
        job_requirements: dict with keys 'job_description', 'required_skills', 'required_experience'

        Returns: {'total_score': float, 'breakdown': {...}}
        """
        # Extract pieces
        candidate_skills = features.get('skills', []) or []
        candidate_text = features.get('processed_text') or ''
        candidate_experience = features.get('experience_years')

        job_desc = job_requirements.get('job_description', '') or ''
        required_skills = job_requirements.get('required_skills', []) or []
        required_experience = job_requirements.get('required_experience', 0) or 0

        skill_s = self._skill_score(candidate_skills, required_skills)
        semantic_s = self._semantic_score(candidate_text, job_desc)
        exp_s = self._experience_score(candidate_experience, required_experience)

        # Weighted sum
        total = (
            self.skill_weight * skill_s
            + self.semantic_weight * semantic_s
            + self.experience_weight * exp_s
        )

        # Normalize to 0..1 (weights may not exactly sum to 1)
        weight_sum = self.skill_weight + self.semantic_weight + self.experience_weight
        if weight_sum > 0:
            total = total / weight_sum

        breakdown = {
            'skill_score': skill_s,
            'semantic_score': semantic_s,
            'experience_score': exp_s,
            'weights': {
                'skill_weight': self.skill_weight,
                'semantic_weight': self.semantic_weight,
                'experience_weight': self.experience_weight
            }
        }

        return {
            'total_score': float(total),
            'breakdown': breakdown
        }
