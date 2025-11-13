document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('jobRequirementsForm');
    const resultsContainer = document.querySelector('.results-container');
    const loadingDiv = document.querySelector('.loading');
    const resultsDiv = document.getElementById('results');
    const exportControls = document.querySelector('.export-controls');
    const exportCsvBtn = document.getElementById('exportCsv');
    const exportJsonBtn = document.getElementById('exportJson');

    // Cache the last results so we can export them
    let candidatesCache = [];

    // File list display
    const fileInput = document.getElementById('resumes');
    const fileList = document.getElementById('fileList');

    fileInput.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        fileList.innerHTML = files.map(file => `
            <div class="file-item">
                <span>${file.name}</span>
                <small>${(file.size / 1024).toFixed(1)} KB</small>
            </div>
        `).join('');
    });

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Show loading state
        resultsContainer.style.display = 'block';
        loadingDiv.style.display = 'block';
        resultsDiv.innerHTML = '';

        try {
            const formData = new FormData(form);
            const response = await fetch('/process_resumes', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            // Hide loading state
            loadingDiv.style.display = 'none';

            if (data.success) {
                // Determine top-N from form (default 3)
                let topN = 3;
                try {
                    const v = parseInt(document.getElementById('topN')?.value || '3', 10);
                    if (!isNaN(v) && v > 0) topN = v;
                } catch (e) {}

                // slice candidates to top-N for display and export
                const allCandidates = data.candidates || [];
                const displayCandidates = allCandidates.slice(0, topN);

                if (displayCandidates.length === 0) {
                    resultsDiv.innerHTML = `<div class="error-message">${data.message || 'No candidates found.'}</div>`;
                    exportControls.style.display = 'none';
                    candidatesCache = [];
                } else {
                    displayResults(displayCandidates);
                    // store for export (only top-N)
                    candidatesCache = displayCandidates;
                    exportControls.style.display = candidatesCache.length > 0 ? 'block' : 'none';
                }
            } else {
                displayError(data.error);
            }
        } catch (error) {
            loadingDiv.style.display = 'none';
            displayError('An error occurred while processing the resumes.');
        }
    });

    function displayResults(candidates) {
        resultsDiv.innerHTML = '';

        // Show only Name, Email, Score and Download link per candidate
        candidates.forEach((candidate, index) => {
            const features = candidate.features || {};
            const name = features.name || '';
            const email = features.email || '';

            const card = document.createElement('div');
            card.className = 'candidate-card minimal';
            card.innerHTML = `
                <div class="candidate-row">
                    <div class="candidate-left">
                        <h3>Rank #${index + 1}: ${name || candidate.filename}</h3>
                        ${email ? `<div><strong>Email:</strong> ${email}</div>` : ''}
                    </div>
                    <div class="candidate-right">
                        <div class="candidate-score">Score: ${candidate.score.toFixed(2)}</div>
                        ${candidate.filename ? `<a href="/download_resume/${encodeURIComponent(candidate.filename)}" class="submit-btn" download>Download Resume</a>` : ''}
                    </div>
                </div>
            `;

            resultsDiv.appendChild(card);
        });

        // Hide export controls since user requested minimal view
        if (exportControls) exportControls.style.display = 'none';
    }

    // Export handlers
    if (exportCsvBtn) exportCsvBtn.addEventListener('click', () => {
        if (!candidatesCache || !candidatesCache.length) return alert('No results to export');
        const csv = convertCandidatesToCSV(candidatesCache);
        downloadFile(csv, 'candidates_ranked.csv', 'text/csv');
    });

    if (exportJsonBtn) exportJsonBtn.addEventListener('click', () => {
        if (!candidatesCache || !candidatesCache.length) return alert('No results to export');
        const jsonStr = JSON.stringify(candidatesCache, null, 2);
        downloadFile(jsonStr, 'candidates_ranked.json', 'application/json');
    });

    function convertCandidatesToCSV(candidates) {
        const headers = ['rank','filename','name','email','phone','experience_years','education','score','matched_skills','summary'];
        const rows = [headers.join(',')];

        candidates.forEach((c, idx) => {
            const f = c.features || {};
            const name = safeCsv(f.name || '');
            const email = safeCsv(f.email || '');
            const phone = safeCsv(f.phone || '');
            const exp = f.experience_years !== undefined && f.experience_years !== null ? f.experience_years : '';
            const education = safeCsv((f.education && f.education.length) ? f.education.join('; ') : '');
            const score = (typeof c.score === 'number') ? c.score : '';
            const skills = safeCsv((f.skills && f.skills.length) ? f.skills.join('; ') : '');
            const summary = safeCsv(f.summary || '');

            const row = [idx+1, c.filename, name, email, phone, exp, education, score, skills, summary];
            rows.push(row.map(v => String(v)).join(','));
        });

        return rows.join('\n');
    }

    function safeCsv(val) {
        if (val === null || val === undefined) return '';
        // escape double quotes
        const s = String(val).replace(/"/g, '""');
        // wrap in quotes if contains comma or newline
        if (s.search(/[,\n"]/g) >= 0) return '"' + s + '"';
        return s;
    }

    function downloadFile(content, filename, mime) {
        const blob = new Blob([content], { type: mime });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function displayError(message) {
        resultsDiv.innerHTML = `
            <div class="error-message">
                ${message}
            </div>
        `;
    }

    // Validate weights sum to 1.0
    const weightInputs = document.querySelectorAll('input[type="number"][name$="weight"]');
    weightInputs.forEach(input => {
        input.addEventListener('change', validateWeights);
    });

    function validateWeights() {
        const skillWeight = parseFloat(document.getElementById('skillWeight').value);
        const experienceWeight = parseFloat(document.getElementById('experienceWeight').value);
        const semanticWeight = parseFloat(document.getElementById('semanticWeight').value);
        
        const sum = skillWeight + experienceWeight + semanticWeight;
        
        if (Math.abs(sum - 1.0) > 0.01) {
            alert('The weights must sum to 1.0');
            return false;
        }
        return true;
    }
});