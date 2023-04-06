import re
from googletrans import Translator

class TextProcessor:
    def __init__(self):
        self.translator = Translator()

    def process_text(self, text):
        cleaned_text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text
    
    def translate_text(self, text, target_language):
        if not text.strip():
            return text
        try:
            translation = self.translator.translate(text, dest=target_language)
            return translation.text
        except Exception as e:
            print(f"Error while translating: {e}")
            return text  
