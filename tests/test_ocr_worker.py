import pytest
import unittest.mock as mock
from queue import Queue
from PIL import Image
from PyQt5.QtCore import Qt
from components.ocr_worker import OCRWorker, upscale_image, adaptive_thresholding, ocr_screenshot

language_test_texts = [
    ("afr", "Toets teks"),
    ("sqi", "Tekst prova"),
    ("amh", "መልኩም ጽሁፍ"),
    ("ara", "نص الاختبار"),
    ("hye", "Փորձառակ տեքստ"),
    ("aze", "Test mətni"),
    ("eus", "Froga testua"),
    ("bel", "Тэставы тэкст"),
    ("ben", "টেস্ট টেক্সট"),
    ("bos", "Testni tekst"),
    ("bul", "Тестов текст"),
    ("cat", "Text de prova"),
    ("ceb", "Teksto sa pagtest"),
    ("chi_sim", "测试文本"),
    ("chi_tra", "測試文本"),
    ("cos", "Testu di prova"),
    ("hrv", "Tekst za testiranje"),
    ("ces", "Testovací text"),
    ("dan", "Testtekst"),
    ("nld", "Testtekst"),
    ("eng", "Test text"),
    ("epo", "Prova teksto"),
    ("est", "Testtekst"),
    ("fin", "Testiteksti"),
    ("fra", "Texte de test"),
    ("fry", "Test tekst"),
    ("glg", "Texto de proba"),
    ("kat", "ტესტის ტექსტი"),
    ("deu", "Testtext"),
    ("ell", "Δοκιμαστικό κείμενο"),
    ("guj", "ટેસ્ટ ટેક્સ્ટ"),
    ("hat", "Tèks tès"),
    ("hau", "Rubutun gwaji"),
    ("haw", "Kikokikona hoʻoia"),
    ("heb", "טקסט לבדיקה"),
    ("hin", "परीक्षण पाठ"),
    ("hun", "Tesztszöveg"),
    ("isl", "Prófunartexti"),
    ("ibo", "Achịkwa okwu"),
    ("ind", "Teks uji"),
    ("gle", "Téacs tástála"),
    ("ita", "Testo di prova"),
    ("jpn", "テストテキスト"),
    ("jav", "Teks tes"),
    ("kan", "ಪರೀಕ್ಷಾ ಪಠ್ಯ"),
    ("kaz", "Сынақ мәтіні"),
    ("khm", "អត្ថបទ​សាក​ល្បង"),
    ("kor", "테스트 텍스트"),
    ("kmr", "Nivîsara testê"),
    ("kir", "Тексти текшерүү"),
    ("lao", "ຂໍ້ຄວາມທົດສອບ"),
    ("lat", "Textus testis"),
    ("lav", "Testa teksts"),
    ("lit", "Testo tekstas"),
    ("ltz", "Testtext"),
    ("mkd", "Тест текст"),
    ("mlg", "Lahatsoratra fandinihana"),
    ("msa", "Teks ujian"),
    ("mal", "പരീക്ഷണ ടെക്സ്റ്റ്"),
    ("mlt", "Test tat-test"),
    ("mri", "Tuhinga whakamātautau"),
    ("mar", "चाचणी मजकूर"),
    ("mon", "Тестийн бичиг"),
    ("nep", "परीक्षा पाठ"),
    ("nor", "Testtekst"),
    ("pus", "ټاسټ متن"),
    ("fas", "متن آزمایشی"),
    ("pol", "Tekst testowy"),
    ("por", "Texto de teste"),
    ("pan", "ਟੈਸਟ ਟੈਕਸਟ"),
    ("ron", "Text de test"),
    ("rus", "Тестовый текст"),
    ("srp", "Тест текст"),
    ("sot", "Lebokoso la tekete"),
    ("sna", "Zvinyorwa zvekunzwisisa"),
    ("snd", "ٽيسٽ متن"),
    ("sin", "පරීක්ෂණ පෙළ"),
    ("slk", "Testovací text"),
    ("slv", "Testno besedilo"),
    ("som", "Qoraal tijaabada"),
    ("spa", "Texto de prueba"),
    ("sun", "Teks tes"),
    ("swa", "Nakala ya jaribio"),
    ("swe", "Testtext"),
    ("tgl", "Teksto ng pagsusuri"),
    ("tgk", "Матни санҷиш"),
    ("tam", "சோதனை உரை"),
    ("tel", "పరీక్షా టెక్స్ట్"),
    ("tha", "ข้อความทดสอบ"),
    ("tur", "Test metni"),
    ("ukr", "Тестовий текст"),
    ("urd", "ٹیسٹ متن"),
    ("uzb", "Test matni"),
    ("vie", "Văn bản kiểm tra"),
    ("cym", "Testun prawf"),
    ("xho", "Uhlolo lolwazi"),
    ("yid", "טעסט טעקסט"),
    ("yor", "Ọrọ ìdánwọ"),
    ("zul", "Umbhalo wokuhlola"),
]

def test_upscale_image():
    image = Image.new("RGB", (50, 50), color="white")
    upscaled_image = upscale_image(image, scale_factor=2)
    
    assert upscaled_image.size == (100, 100)


def test_adaptive_thresholding():
    image = Image.new("RGB", (50, 50), color="white")
    thresholded_image = adaptive_thresholding(image)
    
    assert thresholded_image.mode == "1"

@pytest.mark.parametrize("language_code, expected_text", language_test_texts)
def test_ocr_screenshot(language_code, expected_text):
    image = Image.new("RGB", (50, 50), color="white")

    with mock.patch("pytesseract.image_to_string") as mocked_image_to_string:
        mocked_image_to_string.return_value = expected_text
        text = ocr_screenshot(image, language_code)

    assert text == expected_text

@pytest.mark.parametrize("language_code, expected_text",language_test_texts)
def test_ocr_worker_run(qtbot, language_code, expected_text):
    screenshot_queue = Queue()
    test_image = Image.new("RGB", (50, 50), color="white")
    screenshot_queue.put((test_image, language_code))

    ocr_worker = OCRWorker(screenshot_queue, language_code)

    with mock.patch("components.ocr_worker.ocr_screenshot") as mocked_ocr_screenshot:
        mocked_ocr_screenshot.return_value = expected_text

        with qtbot.wait_signal(ocr_worker.ocr_result, timeout=5000) as blocker:
            ocr_worker.start()
            blocker.wait()
        assert blocker.args == [expected_text]

