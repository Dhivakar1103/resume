# processor.py (improved skills extraction and safe NLP init)
import re
import numpy as np

# spaCy + NLTK with safe initialization
try:
    import spacy
    _SPACY_AVAILABLE = True
except Exception:
    spacy = None
    _SPACY_AVAILABLE = False

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

class NLPProcessor:
    """Process resume text using NLP techniques to extract relevant features."""

    def __init__(self):
        # Try to initialize spaCy model; if not available, fall back to None
        self.nlp = None
        if _SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load('en_core_web_sm')
            except Exception:
                try:
                    from spacy.cli import download
                    download('en_core_web_sm')
                    self.nlp = spacy.load('en_core_web_sm')
                except Exception:
                    self.nlp = None

        # Ensure required NLTK packages are available (best-effort)
        for pkg in ['punkt', 'stopwords']:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            self.stop_words = set(['the','and','is','in','to','of','a','for','on','with'])

    def extract_features(self, text):
        """
        Extract features from resume text.
        Returns a dict with keys:
          name, email, phone, entities (list), embedding (np.array),
          skills (list), experience_years, education (list), summary,
          text_length, processed_text
        """
        text = text or ""
        # basic tokens
        try:
            tokens = [t for t in word_tokenize(text.lower()) if t.isalpha() and t not in self.stop_words]
        except Exception:
            tokens = [t for t in re.findall(r'\b[a-zA-Z]+\b', text.lower()) if t not in self.stop_words]

        # process with spaCy if available
        doc = self.nlp(text) if self.nlp else None

        # entities: collect all occurrences
        entities = []
        if doc:
            for ent in doc.ents:
                entities.append({'label': ent.label_, 'text': ent.text})

        # contact and profile info
        name = self._extract_name(doc, text)
        email, phone = self._extract_contact_info(text)
        experience_years = self._extract_experience_years(text)
        education = self._extract_education(text)
        summary = self._extract_summary(text)

        # embedding: use spaCy vector when available & non-zero, else hashed bag-of-words
        embedding = None
        if doc is not None and hasattr(doc, 'vector'):
            vec = doc.vector
            try:
                if isinstance(vec, (list, tuple, np.ndarray)) and np.linalg.norm(vec) > 1e-9:
                    embedding = np.asarray(vec, dtype=float)
            except Exception:
                embedding = None

        if embedding is None:
            # hashed BOW fallback
            from hashlib import blake2b
            dim = 256
            vec = np.zeros(dim, dtype=float)
            for tok in tokens:
                h = int.from_bytes(blake2b(tok.encode('utf-8'), digest_size=8).digest(), 'little')
                vec[h % dim] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embedding = vec

        # skills extraction (returns list)
        skills = self._extract_skills(text, doc)

        return {
            'name': name,
            'email': email,
            'phone': phone,
            'entities': entities,
            'embedding': embedding,     # single vector
            'skills': skills,          # list
            'experience_years': experience_years,
            'education': education,
            'summary': summary,
            'text_length': len(tokens),
            'processed_text': ' '.join(tokens)
        }

    def _extract_skills(self, text, doc):
        """Extract skills: look in SKILLS section first; then scan curated list in text."""
        # 1) skills section
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
            for l in skills_section:
                parts = re.split(r'[;,|\u2022]', l)
                for p in parts:
                    p = p.strip()
                    if p:
                        extracted.append(p.lower())

        # curated skills
        curated = {
            'python','java','c++','c#','javascript','typescript','sql','mysql','postgresql','mongodb',
            'aws','azure','gcp','docker','kubernetes','git','linux','html','css','react','angular',
            'nodejs','django','flask','spring','selenium','jira','jenkins','ci/cd','pandas','numpy',
            'scikit-learn','tensorflow','keras','pytorch','matplotlib','spark','hadoop','tableau','powerbi',
            'excel','oracle','bash','shell','json','xml','php','.net','postman','pytest','junit','hibernate',
            'express','bootstrap','vue','redis','elasticsearch','graphql','firebase','android','ios','swift',
            'go','ruby','rails','scala','devops','etl','nlp','statistics','scrum','agile'
        }

        found = set()
        # scan extracted list first (from SKILLS section)
        for s in extracted:
            s_norm = re.sub(r'[^a-z0-9\+#\.\-]+','', s.lower())
            # map some common variants
            s_norm = s_norm.replace('node.js','nodejs').replace('ci/cd','cicd').replace('.net','dotnet')
            if s_norm in curated or any(c in s_norm for c in curated):
                # try to map back to curated if possible
                matched = None
                for c in curated:
                    if c in s_norm or s_norm in c:
                        matched = c
                        break
                found.add(matched or s)
        # scan full text tokens for curated skills
        for token in re.findall(r'[a-zA-Z0-9\+#\.\-]+', text.lower()):
            tnorm = token.replace('node.js','nodejs').replace('.net','dotnet')
            if tnorm in curated:
                found.add(tnorm)

        # final sorted list
        skills_list = sorted(found)
        return skills_list

    def _extract_contact_info(self, text):
        """Extract email and phone number using regex."""
        email = None
        phone = None
        m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
        if m:
            email = m.group(0).strip()

        # phone: permissive international pattern
        m = re.search(r'(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?){1,3}\d{3,4}', text)
        if m:
            phone = re.sub(r'\s+', '', m.group(0)).strip()

        return email, phone

    def _extract_name(self, doc, text):
        """Prefer PERSON entity else top non-heading line."""
        if doc:
            for ent in doc.ents:
                if getattr(ent, 'label_', '') == 'PERSON':
                    return ent.text.strip()
        for line in text.splitlines():
            line = line.strip()
            if line and len(line.split()) <= 6 and line.upper() not in ('SUMMARY','OBJECTIVE','SKILLS','EXPERIENCE','EDUCATION'):
                return line
        return None

    def _extract_experience_years(self, text):
        """Heuristic: 'X years' or year ranges."""
        t = text.lower()
        m = re.search(r'(\d+(?:\.\d+)?)(?:\+)?\s+years', t)
        if m:
            try:
                return float(m.group(1))
            except Exception:
                pass
        years = re.findall(r'\b(?:19|20)\d{2}\b', text)
        if years and len(years) >= 2:
            try:
                ys = [int(y) for y in years]
                span = max(ys) - min(ys)
                if span >= 0:
                    return float(span)
            except Exception:
                pass
        return None

    def _extract_education(self, text):
        edu_lines = []
        for line in text.splitlines():
            ll = line.lower()
            if any(k in ll for k in ('bachelor','master','b.sc','m.sc','phd','university','college','btech','mtech','b.e','m.e')):
                edu_lines.append(line.strip())
        return edu_lines

    def _extract_summary(self, text):
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().upper() in ('SUMMARY','PROFESSIONAL SUMMARY','PROFILE','OBJECTIVE'):
                summary_lines = []
                for s in lines[i+1:i+6]:
                    if s.strip():
                        summary_lines.append(s.strip())
                    if len(summary_lines) >= 3:
                        break
                return ' '.join(summary_lines)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        if paragraphs:
            return paragraphs[0][:1000]
        return None
