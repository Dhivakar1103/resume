# main.py  (modified from your original, same structure)
import argparse
import json
from pathlib import Path
import numpy as np
from parser import ResumeParser
from processor import NLPProcessor
# Use the local resume_ranking module (file: src/resume_ranking.py)
from resume_ranking import CandidateRanker

def load_job_requirements(file_path):
    """Load job requirements from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

def process_resumes(job_requirements, resumes_dir):
    """Process resumes and return ranked candidates."""
    # Initialize components
    resume_parser = ResumeParser()
    nlp_processor = NLPProcessor()
    # Extract weights from job_requirements (ensure numeric values)
    skill_w = float(job_requirements.get('skill_weight', 0.4))
    semantic_w = float(job_requirements.get('semantic_weight', 0.3))
    experience_w = float(job_requirements.get('experience_weight', 0.3))
    candidate_ranker = CandidateRanker(skill_w, semantic_w, experience_w)

    # Process resumes
    results = []
    resumes_dir = Path(resumes_dir)
    print(f"\nSearching for resumes in: {resumes_dir}")
    
    found_files = list(resumes_dir.glob('*.*'))
    if not found_files:
        print(f"No files found in {resumes_dir}")
        return []
        
    print(f"Found {len(found_files)} files")
    
    for resume_file in found_files:
        print(f"\nProcessing: {resume_file.name}")
        if resume_file.suffix.lower() in ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            try:
                # Parse resume
                print("- Parsing resume...")
                resume_text = resume_parser.parse(str(resume_file)) or ""

                # Process with NLP
                print("- Extracting features...")
                features = nlp_processor.extract_features(resume_text)

                # Score candidate (ranker returns dict with total_score 0..10)
                print("- Scoring candidate...")
                score_obj = candidate_ranker.score_candidate(features, job_requirements)
                # CandidateRanker returns a 0..1 total_score; scale to 0..10 for UI
                score = float(score_obj.get('total_score', 0.0)) * 10.0

                # Convert numpy types to Python native types
                processed_features = convert_numpy_types(features)

                results.append({
                    'filename': resume_file.name,
                    'score': float(score),  # already 0..10 scale
                    'features': processed_features,
                    'breakdown': score_obj.get('breakdown', {})
                })
                print(f"- Successfully processed {resume_file.name}")
            except Exception as e:
                print(f"Error processing {resume_file.name}: {str(e)}")
        else:
            print(f"Skipping unsupported file format: {resume_file.name}")

    # Sort results by score
    return sorted(results, key=lambda x: x['score'], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='AI-Powered Resume Screening System')
    parser.add_argument('--job-requirements', required=True, help='Path to job requirements JSON file')
    parser.add_argument('--resumes-dir', default='../test_resumes', help='Directory containing resumes')
    args = parser.parse_args()

    # Load job requirements
    job_requirements = load_job_requirements(args.job_requirements)
    
    # Process resumes
    ranked_candidates = process_resumes(job_requirements, args.resumes_dir)

    # Output results
    print("\nRanked Candidates:")
    print("-----------------")
    for rank, candidate in enumerate(ranked_candidates, 1):
        print(f"{rank}. {candidate['filename']} - Score: {candidate['score']:.2f}")
        feats = candidate.get('features', {})
        # display email/phone safely
        if feats.get('email'):
            print(f"   Email: {feats['email']}")
        if feats.get('phone'):
            print(f"   Phone: {feats['phone']}")
        if feats.get('experience_years') is not None:
            print(f"   Experience (years): {feats['experience_years']}")
        if feats.get('education'):
            print(f"   Education: {', '.join(feats['education'])}")
        if feats.get('summary'):
            print(f"   Summary: {feats['summary']}")
        if feats.get('skills'):
            print(f"   Matched Skills: {', '.join(feats['skills'])}")
        print()

if __name__ == '__main__':
    main()
