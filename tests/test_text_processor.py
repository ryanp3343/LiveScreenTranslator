import pytest
from components.text_processor import TextProcessor

language_test_texts = [
    ("af", "hallo"),
    ("sq", "përshëndetje"),
    ("am", "ሰላም"),
    ("ar", "مرحبا"),
    ("hy", "բարև"),
    ("az", "salam"),
    ("eu", "kaixo"),
    ("be", "прывітанне"),
    ("bn", "হ্যালো"),
    ("bs", "zdravo"),
    ("bg", "здравейте"),
    ("ca", "hola"),
    ("ceb", "hello"),
    ("zh-cn", "你好"),
    ("zh-tw", "你好"),
    ("co", "bonghjornu"),
    ("hr", "zdravo"),
    ("cs", "ahoj"),
    ("da", "hej"),
    ("nl", "hallo"),
    ("en", "hello"),
    ("eo", "saluton"),
    ("et", "tere"),
    ("fi", "hei"),
    ("fr", "bonjour"),
    ("gl", "hola"),
    ("ka", "გამარჯობა"),
    ("de", "hallo"),
    ("el", "γεια σου"),
    ("gu", "હેલો"),
    ("ht", "bonjou"),
    ("ha", "sannu"),
    ("haw", "aloha"),
    ("he", "שלום"),
    ("hi", "नमस्ते"),
    ("hu", "szia"),
    ("is", "hæ"),
    ("ig", "Ndewo"),
    ("id", "halo"),
    ("ga", "dia dhuit"),
    ("it", "ciao"),
    ("ja", "こんにちは"),
    ("jw", "halo"),
    ("kn", "ಹಲೋ"),
    ("kk", "сәлем"),
    ("km", "ជំរាបសួរ"),
    ("ko", "안녕하세요"),
    ("ku", "silav"),
    ("ky", "салам"),
    ("lo", "ສະບາຍດີ"),
    ("la", "salve"),
    ("lv", "sveiki"),
    ("lt", "labas"),
    ("lb", "hallo"),
    ("mk", "здраво"),
    ("mg", "manao ahoana"),
    ("ms", "hello"),
    ("ml", "ഹലോ"),
    ("mt", "hello"),
    ("mi", "kia ora"),
    ("mr", "नमस्कार"),
    ("mn", "сайн уу"),
    ("ne", "नमस्कार"),
    ("no", "hei"),
    ("ps", "سلام"),
    ("fa", "سلام"),
    ("pl", "cześć"),
    ("pt", "olá"),
    ("pa", "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ"),
    ("ro", "salut"),
    ("ru", "здравствуйте"),
    ("sr", "Здраво"),
    ("st", "Dumela"),
    ("sn", "Mhoro"),
    ("sd", "هيلو"),
    ("si", "හෙලෝ"),
    ("sk", "Ahoj"),
    ("sl", "Pozdravljeni"),
    ("so", "Maalim wanaag"),
    ("es", "Hola"),
    ("su", "halo"),
    ("sw", "Habari"),
    ("sv", "Hej"),
    ("tl", "Kamusta"),
    ("tg", "Салом"),
    ("ta", "வணக்கம்"),
    ("te", "హలో"),
    ("th", "สวัสดี"),
    ("tr", "Merhaba"),
    ("uk", "Привіт"),
    ("ur", "ہیلو"),
    ("uz", "Salom"),
    ("vi", "Xin chào"),
    ("cy", "Helo"),
    ("xh", "Molo"),
    ("yi", "העלא"),
    ("yo", "Bawo"),
    ("zu", "Sawubona")
]

def test_process_text():
    text_processor = TextProcessor()
    input_text = "Hello, world! \nThis is a test.\n"
    expected_output = "Hello world This is a test"
    assert text_processor.process_text(input_text) == expected_output


@pytest.mark.parametrize("language_code, _", language_test_texts)
def test_translate_text(language_code, _):
    text_processor = TextProcessor()
    source_text = "Hello"
    try:
        text_processor.translate_text(source_text, language_code)
    except ValueError:
        pytest.fail(f"Invalid destination language: {language_code}")



@pytest.mark.parametrize("language_code, _", language_test_texts)
def test_remove_stopwords(language_code, _):
    if language_code in ["az", "ca", "nl", "hu", "it", "pt", "ro", "es"]:
        pytest.skip(f"Unsupported language: {language_code}")
    else:
        text_processor = TextProcessor()
        input_text = "This is a test sentence with some common English stopwords"
        expected_output = "test sentence common English stopwords"
        result = text_processor.remove_stopwords(input_text, language_code)
        if language_code == "en":
            assert result == expected_output
        else:
            assert result == input_text



def test_calculate_similarity():
    text_processor = TextProcessor()
    text1 = "This is a test sentence with some common English stopwords"
    text2 = "A test sentence containing a few frequent English stopwords"
    language_code = "en"
    similarity = text_processor.calculate_similarity(text1, text2, language_code)
    assert 0.5 < similarity < 1
