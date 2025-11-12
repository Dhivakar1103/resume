import argparse
import json
from pathlib import Path
import numpy as np

from parser import ResumeParser
from processor import NLPProcessor
from resume_ranking import CandidateRanker


def load_job_requirements(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def convert_numpy_types(obj):
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
    resume_parser = ResumeParser()
    nlp_processor = NLPProcessor()
    ranker = CandidateRanker()

    results = []
    resumes_dir = Path(resumes_dir)
    print(f"\nSearching: {resumes_dir}")

    files = list(resumes_dir.glob("*.*"))
    if not files:
        print("No resumes found")
        return []

    for f in files:
        print(f"\nProcessing: {f.name}")

        if f.suffix.lower() not in [
            ".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"
        ]:
            print("Skipping unsupported:", f.name)
            continue

        try:
            text = resume_parser.parse(str(f))
            features = nlp_processor.extract_features(text)
            scored = ranker.score_candidate(features, job_requirements)

            features = convert_numpy_types(features)

            results.append({
                "filename": f.name,
                "score": float(scored["total_score"]),
                "breakdown": convert_numpy_types(scored["breakdown"]),
                "features": features
            })
        except Exception as e:
            print("Error:", e)

    return sorted(results, key=lambda x: x["score"], reverse=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-requirements", required=True)
    parser.add_argument("--resumes-dir", default="../test_resumes")
    args = parser.parse_args()

    req = load_job_requirements(args.job_requirements)
    ranked = process_resumes(req, args.resumes_dir)

    print("\nFinal Ranking:")
    for i, c in enumerate(ranked, 1):
        print(f"{i}. {c['filename']}  Score={c['score']:.2f}")


if __name__ == "__main__":
    main()
