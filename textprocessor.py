import re
import nltk
from googletrans import Translator

class TextProcessor:
    def __init__(self):
        self.translator = Translator()

    def process_text(self, text):
        # Remove all non-alphanumeric characters using a regular expression
        cleaned_text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        return cleaned_text
    
    def translate_text(self, text, target_language):
        translation = self.translator.translate(text, dest=target_language)
        return translation.text