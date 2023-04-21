from googletrans import LANGUAGES
from googletrans import Translator
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)


class TextProcessor:
    """
    Processes the text from ocr cleans, translates sends back to mainwindow
    also added cosine similarity so the same text doesnt get outputed
    """

    def __init__(self):
        """Init googletrans"""
        self.translator = Translator()

    def process_text(self, text):
        """uses regex to remove special chars and whitespace"""
        cleaned_text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned_text

    def translate_text(self, text, target_language):
        """using googletrans api to translate giving text with language code"""
        if not text.strip():
            return text
        try:
            translation = self.translator.translate(text, dest=target_language)
            return translation.text
        except Exception as e:
            print(f"Error while translating: {e}")
            return text

    def remove_stopwords(self, text, language_code):
        """removes stopwords for cosine similarity based on their language"""
        if language_code not in LANGUAGES:
            return text

        lang = LANGUAGES[language_code]
        if lang not in stopwords.fileids():
            return text

        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)

        stop_words = set(stopwords.words(lang))
        word_tokens = word_tokenize(text)
        return " ".join(
            [word for word in word_tokens if word.lower() not in stop_words]
        )


    def calculate_similarity(self, text1, text2, language_code):
        """calculates the cosine similarity between the current and previous text sent"""
        filtered_text1 = self.remove_stopwords(text1, language_code)
        filtered_text2 = self.remove_stopwords(text2, language_code)

        if not filtered_text1 or not filtered_text2:
            return 0

        vectorizer = TfidfVectorizer().fit([filtered_text1, filtered_text2])
        tfidf_matrix = vectorizer.transform([filtered_text1, filtered_text2])

        cosine_similarities = cosine_similarity(tfidf_matrix)
        return cosine_similarities[0, 1]
