import re
import numpy as np
import nltk

# Try loading spaCy safely
try:
    import spacy
    try:
        NLP_CORE = spacy.load("en_core_web_sm")
    except Exception:
        NLP_CORE = spacy.blank("en")     # fallback if model missing
except Exception:
    NLP_CORE = None

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


class NLPProcessor:
    """Process resume text using NLP techniques to extract relevant features."""

    def __init__(self):
        # Ensure required NLTK packages (quiet mode)
        required = ['punkt', 'stopwords', 'averaged_perceptron_tagger', 'wordnet']
        for pkg in required:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass

        # Load stopwords (backup list if download fails)
        try:
            self.stop_words = set(stopwords.words("english"))
        except Exception:
            self.stop_words = {"the", "and", "is", "in", "to", "of", "for"}

        # spaCy pipeline
        self.nlp = NLP_CORE

    def extract_features(self, text):
        """Extract features from resume text."""
        if not text:
            text = ""

        # Basic preprocessing
        tokens = []
        try:
            tokens = [t for t in word_tokenize(text.lower()) if t.isalpha() and t not in self.stop_words]
        except Exception:
            tokens = text.lower().split()

        # spaCy doc
        doc = self.nlp(text) if self.nlp else None

        # Extract entities safely
        entities = {}
        if doc:
            for ent in doc.ents:
                entities.setdefault(ent.label_, []).append(ent.text)

        # Extract details
        name = self._extract_name(doc, text)
        email, phone = self._extract_contact_info(text)
        experience_years = self._extract_experience_years(text)
        education = self._extract_education(text)
        summary = self._extract_summary(text)

        # Embeddings: spaCy vector or fallback hashed vector
        embeddings = self._get_embeddings(doc, tokens)

        # Extract skills
        skills = self._extract_skills(doc, text)

        return {
            "name": name,
            "email": email,
            "phone": phone,
            "entities": entities,
            "embeddings": embeddings,
            "skills": skills,
            "experience_years": experience_years,
            "education": education,
            "summary": summary,
            "text_length": len(tokens),
            "processed_text": " ".join(tokens)
        }

    # ----------------------------------------------------------------------
    # ✅ improved embedding extraction
    # ----------------------------------------------------------------------
    def _get_embeddings(self, doc, tokens):
        """Return either spaCy vector or hashed fallback embeddings."""
        if doc is not None and hasattr(doc, "vector"):
            vec = np.asarray(doc.vector, dtype=float)
            if vec.size > 0 and np.linalg.norm(vec) > 1e-9:
                return vec.reshape(1, -1)

        # Fallback hashed embedding
        from hashlib import blake2b
        dim = 256
        vec = np.zeros(dim, dtype=float)

        for t in tokens:
            h = int.from_bytes(blake2b(t.encode("utf-8"), digest_size=8).digest(), "little")
            vec[h % dim] += 1.0

        if np.linalg.norm(vec) > 0:
            vec /= np.linalg.norm(vec)

        return vec.reshape(1, -1)

    # ----------------------------------------------------------------------
    # ✅ improved skills extraction
    # ----------------------------------------------------------------------
    def _extract_skills(self, doc, text):
        """Extract skills from SKILLS section + curated list + fallback scanning."""
        lines = text.splitlines()
        in_skills = False
        skills_block = []

        # Detect SKILLS section
        for line in lines:
            if in_skills:
                if line.strip() == "" or re.match(r"^[A-Z ]{3,}$", line.strip()):
                    break
                skills_block.append(line.strip())

            if line.strip().upper() == "SKILLS":
                in_skills = True

        # Normalize extracted raw skills
        raw = []
        for line in skills_block:
            raw += re.split(r"[;,\|\u2022]", line)
        raw = [s.strip().lower() for s in raw if s.strip()]

        # Curated tech skill list
        curated = set([
            'python','java','c','c++','javascript','typescript','sql','mysql','postgresql','mongodb',
            'aws','azure','gcp','docker','kubernetes','git','linux','html','css','react','angular','node.js',
            'django','flask','spring','selenium','jira','jenkins','ci/cd','rest','api','pandas','numpy',
            'scikit-learn','tensorflow','keras','pytorch','matplotlib','spark','hadoop','tableau','powerbi',
            'excel','oracle','bash','shell','json','xml','php','.net','postman','pytest','unittest','junit',
            'hibernate','express','bootstrap','vue','redis','elasticsearch','graphql','firebase','android',
            'ios','swift','objective-c','go','ruby','rails','scala','devops','etl','nlp','statistics',
            'analysis','agile','scrum','kanban'
        ])

        found = set()

        # Match curated skills in text
        for word in re.findall(r"[a-zA-Z][a-zA-Z0-9+\-\.#]*", text.lower()):
            if word in curated:
                found.add(word)

        # Normalize raw-SKILLS with curated list
        normalized_raw = set()
        for skill in raw:
            if skill in curated:
                normalized_raw.add(skill)

        return sorted(found.union(normalized_raw))

    # ----------------------------------------------------------------------
    def _extract_contact_info(self, text):
        email = None
        phone = None

        # Email
        m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if m:
            email = m.group(0)

        # Phone (international-friendly)
        m = re.search(r"(?:\+?\d{1,3}[-\s]?)?(?:\(\d{2,4}\)|\d{3,4})[-\s]?\d{3}[-\s]?\d{3,4}", text)
        if m:
            phone = m.group(0)

        return email, phone

    # ----------------------------------------------------------------------
    def _extract_name(self, doc, text):
        if doc:
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text

        # fallback: first line that looks like a name
        for line in text.splitlines():
            line = line.strip()
            if line and len(line.split()) <= 4:
                if line.upper() not in {"SUMMARY", "EXPERIENCE", "SKILLS", "EDUCATION", "OBJECTIVE"}:
                    return line
        return None

    # ----------------------------------------------------------------------
    def _extract_experience_years(self, text):
        text_low = text.lower()

        # Pattern: "3 years", "5+ years"
        m = re.search(r"(\d+(?:\.\d+)?)(?:\+)?\s+years", text_low)
        if m:
            try:
                return float(m.group(1))
            except:
                pass

        # Pattern: "2018 - 2021"
        years = re.findall(r"\b(?:19|20)\d{2}\b", text)
        if len(years) >= 2:
            try:
                y = list(map(int, years))
                return float(max(y) - min(y))
            except:
                pass

        return None

    # ----------------------------------------------------------------------
    def _extract_education(self, text):
        result = []
        for line in text.splitlines():
            ll = line.lower()
            if any(k in ll for k in [
                "bachelor","master","b.sc","m.sc","phd","university","college","b.tech","m.tech","b.e","m.e"
            ]):
                result.append(line.strip())
        return result

    # ----------------------------------------------------------------------
    def _extract_summary(self, text):
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.strip().upper() in {"SUMMARY","PROFESSIONAL SUMMARY","PROFILE","OBJECTIVE"}:
                collected = []
                for nxt in lines[i+1:i+6]:
                    if nxt.strip():
                        collected.append(nxt.strip())
                return " ".join(collected)

        # fallback: first paragraph
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        return parts[0] if parts else None
