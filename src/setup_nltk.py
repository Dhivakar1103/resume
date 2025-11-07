import nltk
import sys

def download_nltk_resources():
    """Download required NLTK resources."""
    resources = [
        'punkt',
        'stopwords',
        'averaged_perceptron_tagger',
        'wordnet',
        'punkt_tab'
    ]
    
    for resource in resources:
        print(f"Downloading {resource}...")
        try:
            nltk.download(resource)
            print(f"Successfully downloaded {resource}")
        except Exception as e:
            print(f"Error downloading {resource}: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    download_nltk_resources()