import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class CandidateRanker:
    """Rank candidates based on their resume features and job requirements."""
    
    def score_candidate(self, features, job_requirements):
        """
        Score a candidate based on their resume features and job requirements.
        
        Args:
            features (dict): Extracted features from the resume
            job_requirements (dict): Job requirements and weights
            
        Returns:
            float: Candidate score
        """
        score = 0.0
        
        # Score based on skills match
        if 'required_skills' in job_requirements:
            skill_score = self._calculate_skill_score(
                features['skills'],
                job_requirements['required_skills']
            )
            score += skill_score * job_requirements.get('skill_weight', 0.4)
        
        # Score based on semantic similarity
        if 'job_description' in job_requirements:
            semantic_score = self._calculate_semantic_similarity(
                features['embeddings'],
                job_requirements['job_description']
            )
            score += semantic_score * job_requirements.get('semantic_weight', 0.3)
        
        # Score based on experience (if available)
        if 'required_experience' in job_requirements and 'experience' in features['entities']:
            exp_score = self._calculate_experience_score(
                features['entities']['experience'],
                job_requirements['required_experience']
            )
            score += exp_score * job_requirements.get('experience_weight', 0.3)
        
        # Scale score to be out of 10 for easier human interpretation
        return float(score * 10.0)
    
    def _calculate_skill_score(self, candidate_skills, required_skills):
        """Calculate score based on matching skills."""
        if not candidate_skills or not required_skills:
            return 0.0
        
        # Convert to sets for easier matching
        candidate_skills = set(s.lower() for s in candidate_skills)
        required_skills = set(s.lower() for s in required_skills)
        
        # Calculate match percentage
        matched_skills = candidate_skills.intersection(required_skills)
        return len(matched_skills) / len(required_skills)
    
    def _calculate_semantic_similarity(self, candidate_embedding, job_description):
        """Calculate semantic similarity between resume and job description."""
        # This is a placeholder - you would need to process the job description
        # similarly to how resumes are processed to get comparable embeddings
        return float(np.mean(candidate_embedding))  # Simplified for example
    
    def _calculate_experience_score(self, candidate_experience, required_experience):
        """Calculate score based on years of experience."""
        try:
            candidate_years = float(candidate_experience)
            required_years = float(required_experience)
            
            if candidate_years >= required_years:
                return 1.0
            else:
                return candidate_years / required_years
        except (ValueError, TypeError):
            return 0.0