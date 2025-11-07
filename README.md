# AI-Powered Resume Screening System

A sophisticated resume screening system that uses Natural Language Processing (NLP) to analyze resumes and rank candidates based on job requirements.

## Features

- Parse multiple resume formats (PDF, DOCX)
- Extract key information using NLP
- Score candidates based on job requirements
- Generate ranked candidate lists
- Support for custom scoring criteria

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Download required NLTK data:
   ```
   python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger'); nltk.download('wordnet')"
   ```
5. Download spaCy model:
   ```
   python -m spacy download en_core_web_md
   ```

## Usage

1. Place resumes in the `data/resumes` directory
2. Define job requirements in a JSON file
3. Run the screening system:
   ```
   python src/main.py --job-requirements path/to/requirements.json
   ```

## Project Structure

```
resume_screening/
├── data/               # Directory for resumes and job requirements
├── src/               # Source code
│   ├── main.py        # Main application entry point
│   ├── parser.py      # Resume parsing module
│   ├── processor.py   # NLP processing module
│   └── ranking.py     # Candidate ranking module
├── tests/             # Test files
└── requirements.txt   # Project dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.