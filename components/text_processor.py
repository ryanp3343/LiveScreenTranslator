import re
from googletrans import Translator

class TextProcessor:
    def __init__(self):
        self.translator = Translator()

    #regex for special characters and mulitple languages and empty space and endl
    def process_text(self, text):
        cleaned_text = re.sub(r'[^\w\s]', '', text, flags=re.UNICODE)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        # print(cleaned_text)
        return cleaned_text
    
    #use googletrans execption handling for translating bad text
    def translate_text(self, text, target_language):
        if not text.strip():
            return text
        try:
            translation = self.translator.translate(text, dest=target_language)
            return translation.text
        except Exception as e:
            print(f"Error while translating: {e}")
            return text  
