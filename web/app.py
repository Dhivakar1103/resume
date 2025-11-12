import sys
import os
from pathlib import Path

# Add the src directory to Python path FIRST, before any other imports
src_path = str(Path(__file__).parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import urllib.parse
import json

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

        # Handle uploaded resume files (if any)
        resumes_root = Path(__file__).parent.parent / 'test_resumes'
        resumes_root.mkdir(parents=True, exist_ok=True)

        upload_files = request.files.getlist('resumes') if 'resumes' in request.files else []
        if upload_files:
            # create a timestamped subdirectory to avoid mixing with existing files
            from datetime import datetime
            ts = datetime.now().strftime('%Y%m%d%H%M%S')
            upload_dir = resumes_root / f'uploads_{ts}'
            upload_dir.mkdir(parents=True, exist_ok=True)

            saved = []
            for f in upload_files:
                if f and f.filename:
                    filename = secure_filename(f.filename)
                    # prevent empty filenames
                    if filename:
                        target = upload_dir / filename
                        f.save(str(target))
                        saved.append(str(target))

            # Process only uploaded files
            ranked_candidates = process_resumes(job_requirements, upload_dir)
        else:
            # No uploads — process files already in test_resumes
            ranked_candidates = process_resumes(job_requirements, resumes_root)

        # Provide some debug info in the response to help frontend diagnose empty results
        resp = {
            'success': True,
            'candidates': ranked_candidates,
            'processed_count': len(ranked_candidates)
        }
        if not ranked_candidates:
            resp['message'] = 'No candidates were processed. Check uploads and server logs.'
        return jsonify(resp)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

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