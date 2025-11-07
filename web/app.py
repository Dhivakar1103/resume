from flask import Flask, render_template, request, jsonify, send_from_directory, abort
import urllib.parse
import sys
from pathlib import Path
import json

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from main import process_resumes

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_resumes', methods=['POST'])
def process():
    try:
        # Get job requirements from form
        job_requirements = {
            "job_description": request.form.get('job_description', ''),
            "required_skills": [s.strip() for s in request.form.get('required_skills', '').split(',') if s.strip()],
            "required_experience": float(request.form.get('required_experience', 0)),
            "skill_weight": float(request.form.get('skill_weight', 0.4)),
            "semantic_weight": float(request.form.get('semantic_weight', 0.3)),
            "experience_weight": float(request.form.get('experience_weight', 0.3))
        }

        # Save job requirements
        with open(Path(__file__).parent.parent / 'data' / 'job_requirements.json', 'w') as f:
            json.dump(job_requirements, f, indent=4)

        # Process resumes
        resumes_dir = Path(__file__).parent.parent / 'test_resumes'
        ranked_candidates = process_resumes(job_requirements, resumes_dir)

        return jsonify({
            'success': True,
            'candidates': ranked_candidates
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

# Route to download resume files
@app.route('/download_resume/<filename>')
def download_resume(filename):
    # Resume files are in ../test_resumes
    resumes_dir = Path(__file__).parent.parent / 'test_resumes'
    # Security: only allow files in resumes_dir
    safe_filename = Path(urllib.parse.unquote(filename)).name
    file_path = resumes_dir / safe_filename
    if not file_path.exists():
        abort(404)
    return send_from_directory(resumes_dir, safe_filename, as_attachment=True)