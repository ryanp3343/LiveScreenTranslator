import re
import nltk

class TextProcessor:
    def __init__(self):
        pass

    def process_text(self, text):
        # Remove all non-alphanumeric characters using a regular expression
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

        return cleaned_text