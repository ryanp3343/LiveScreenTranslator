import re
from googletrans import Translator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from googletrans import LANGUAGES

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
    def remove_stopwords(self,text, language_code):
            if language_code not in LANGUAGES:
                return text

            lang = LANGUAGES[language_code]
            if lang not in stopwords.fileids():
                return text

            stop_words = set(stopwords.words(lang))
            word_tokens = word_tokenize(text)
            return ' '.join([word for word in word_tokens if word.lower() not in stop_words])

    def calculate_similarity(self, text1, text2, language_code):

        filtered_text1 = self.remove_stopwords(text1, language_code)
        filtered_text2 = self.remove_stopwords(text2, language_code)

        if not filtered_text1 or not filtered_text2:
            return 0

        vectorizer = TfidfVectorizer().fit([filtered_text1, filtered_text2])
        tfidf_matrix = vectorizer.transform([filtered_text1, filtered_text2])

        cosine_similarities = cosine_similarity(tfidf_matrix)
        return cosine_similarities[0, 1]
        
    

