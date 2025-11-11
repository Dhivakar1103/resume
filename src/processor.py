import re
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import numpy as np

class NLPProcessor:
    """Process resume text using NLP techniques to extract relevant features."""
    
    def __init__(self):
        # Load spaCy model (smaller model)
        self.nlp = spacy.load('en_core_web_sm')
        
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
    
    def extract_features(self, text):
        """
        Extract features from resume text.
        
        Args:
            text (str): Resume text content
            
        Returns:
            dict: Extracted features
        """
        # Basic text preprocessing
        tokens = word_tokenize(text.lower())
        tokens = [t for t in tokens if t not in self.stop_words]
        
        # Process with spaCy
        doc = self.nlp(text)

        # Extract named entities
        entities = {ent.label_: ent.text for ent in doc.ents}

        # Extract contact and profile info
        name = self._extract_name(doc, text)
        email, phone = self._extract_contact_info(text)
        experience_years = self._extract_experience_years(text)
        education = self._extract_education(text)
        summary = self._extract_summary(text)

        # Get embeddings from spaCy (lightweight alternative to BERT)
        doc_embed = self.nlp(text)
        embeddings = doc_embed.vector.reshape(1, -1) if doc_embed.vector.shape[0] > 0 else np.zeros((1, 96))
        
        # Extract skills (customize based on your needs)
        skills = self._extract_skills(doc)
        
        return {
            'name': name,
            'email': email,
            'phone': phone,
            'entities': entities,
            'embeddings': embeddings,
            'skills': skills,
            'experience_years': experience_years,
            'education': education,
            'summary': summary,
            'text_length': len(tokens),
            'processed_text': ' '.join(tokens)
        }
    
    def _extract_skills(self, doc):
        """Extract skills from the document, prioritizing SKILLS section and using a curated list."""
        import re
        # 1. Try to extract from SKILLS section
        text = doc.text
        skills_section = []
        lines = text.splitlines()
        in_skills = False
        for line in lines:
            if in_skills:
                if line.strip() == '' or re.match(r'^[A-Z ]{3,}$', line.strip()):
                    break
                skills_section.append(line.strip())
            if line.strip().upper() == 'SKILLS':
                in_skills = True
        extracted = []
        if skills_section:
            # Flatten and split by comma/semicolon/space
            for l in skills_section:
                extracted += re.split(r'[;,|\n]', l)
            extracted = [s.strip() for s in extracted if s.strip()]
        
        # 2. Use a curated list of common tech skills (expand as needed)
        curated_skills = set([
            'python', 'java', 'c++', 'c#', 'javascript', 'typescript', 'sql', 'mysql', 'postgresql', 'mongodb',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'linux', 'html', 'css', 'react', 'angular',
            'node.js', 'django', 'flask', 'spring', 'selenium', 'jira', 'jenkins', 'ci/cd', 'oop', 'rest',
            'api', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'keras', 'pytorch', 'matplotlib', 'spark',
            'hadoop', 'tableau', 'powerbi', 'excel', 'oracle', 'bash', 'shell', 'json', 'xml', 'php', 'dotnet',
            'postman', 'pytest', 'unittest', 'junit', 'hibernate', 'express', 'bootstrap', 'vue', 'typescript',
            'redis', 'elasticsearch', 'graphql', 'firebase', 'android', 'ios', 'swift', 'objective-c', 'go',
            'ruby', 'rails', 'perl', 'scala', 'cloud', 'devops', 'automation', 'testing', 'webdriver', 'oop',
            'api', 'ci', 'cd', 'etl', 'data', 'ml', 'ai', 'nlp', 'statistics', 'analysis', 'pipelines', 'scrum',
            'agile', 'kanban', 'leadership', 'communication', 'problem solving', 'teamwork', 'project management'
        ])
        # Add job requirement skills if available
        try:
            import json
            with open('data/job_requirements.json', 'r') as f:
                job_req = json.load(f)
            for s in job_req.get('required_skills', []):
                curated_skills.add(s.strip().lower())
        except Exception:
            pass
        # 3. Scan doc for curated skills
        found_curated = set()
        for token in doc:
            t = token.text.lower()
            if t in curated_skills:
                found_curated.add(t)
        # 4. Combine and clean
        all_skills = set()
        # Add from SKILLS section if present
        for s in extracted:
            s_clean = s.lower().replace('ci /cd', 'ci/cd').replace('ci / cd', 'ci/cd').replace(' ', '').replace('-', '').replace('_', '')
            for c in curated_skills:
                c_clean = c.replace(' ', '').replace('-', '').replace('_', '')
                if s_clean == c_clean or c in s.lower():
                    all_skills.add(c)
        # Add curated found in doc
        all_skills.update(found_curated)
        # Remove emails, names, and unrelated tokens
        all_skills = [s for s in all_skills if not re.match(r'^[\w\.-]+@[\w\.-]+$', s)]
        # Return sorted for consistency
        return sorted(all_skills)

    def _extract_contact_info(self, text):
        """Extract email and phone number using regex."""
        email = None
        phone = None
        # Simple email regex
        m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
        if m:
            email = m.group(0)

        # Simple phone regex (matches various formats)
        m = re.search(r'(?:\+?\d{1,3}[\s-]?)?(?:\(\d{3}\)|\d{3})[\s-]?\d{3}[\s-]?\d{4}', text)
        if m:
            phone = m.group(0)

        return email, phone

    def _extract_name(self, doc, text):
        """Try to extract the candidate's name. Prefer PERSON entities, else first non-empty line."""
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                return ent.text

        # Fallback: first non-empty line (assuming name at top)
        for line in text.splitlines():
            line = line.strip()
            if line and len(line.split()) <= 6:
                # ignore headings like SUMMARY
                if line.upper() not in ('SUMMARY', 'OBJECTIVE', 'SKILLS', 'EXPERIENCE', 'EDUCATION'):
                    return line
        return None

    def _extract_experience_years(self, text):
        """Extract years of experience from text using heuristic patterns."""
        text_lower = text.lower()
        # Look for patterns like '3 years', '5+ years', 'years of experience'
        m = re.search(r'(\d+(?:\.\d+)?)(?:\+)?\s+years', text_lower)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                return None

        # Try to find ranges like '2018 - 2021' and estimate years
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        if years and len(years) >= 2:
            try:
                y = [int(y) for y in years]
                span = max(y) - min(y)
                return float(span)
            except Exception:
                return None
        return None

    def _extract_education(self, text):
        """Extract education lines mentioning degrees or universities."""
        edu_lines = []
        for line in text.splitlines():
            line_lower = line.lower()
            if any(k in line_lower for k in ('bachelor', 'master', "b.sc", "m.sc", 'phd', 'university', 'college')):
                if line.strip():
                    edu_lines.append(line.strip())
        return edu_lines

    def _extract_summary(self, text):
        """Extract a short summary paragraph from the resume if present."""
        # Look for SUMMARY or PROFESSIONAL SUMMARY headings
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().upper() in ('SUMMARY', 'PROFESSIONAL SUMMARY', 'PROFILE', 'OBJECTIVE'):
                # take next 3 non-empty lines as summary
                summary_lines = []
                for s in lines[i+1:i+6]:
                    if s.strip():
                        summary_lines.append(s.strip())
                    if len(summary_lines) >= 3:
                        break
                return ' '.join(summary_lines)
        # Fallback: first paragraph
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if paragraphs:
            return paragraphs[0][:1000]
        return None