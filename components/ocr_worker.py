from PIL import Image
import pytesseract
from PyQt5.QtCore import QThread, pyqtSignal


def upscale_image(image, scale_factor=2.0):
    """upscale image by scale faction using antialiaising"""
    width, height = image.size
    new_width, new_height = int(width * scale_factor), int(height * scale_factor)
    return image.resize((new_width, new_height), Image.ANTIALIAS)


def adaptive_thresholding(image):
    """adaptive threasholidng to make the image more readable for ocr"""
    gray_image = image.convert("L")
    return gray_image.point(lambda x: 0 if x < 128 else 255, "1")


def ocr_screenshot(image, language_code):
    """run pytesseract given language code"""
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
    config = f"-l {language_code} --psm 6 --oem 1"
    return pytesseract.image_to_string(image, config=config)


class OCRWorker(QThread):
    """
    contantly runs ocr on the screenshots given applying image processing
    and returns text result
    """

    ocr_result = pyqtSignal(str)

    def __init__(self, screenshot_queue, language_combo):
        """Init with screenshot queue and language code"""
        super(OCRWorker, self).__init__()
        self.screenshot_queue = screenshot_queue
        self.language_combo = language_combo

    def run(self):
        """continuous proccess images from queue, get ocr, and return the text"""
        while True:
            screenshot, language_code = self.screenshot_queue.get()
            screenshot = upscale_image(screenshot)
            screenshot = adaptive_thresholding(screenshot)
            text = ocr_screenshot(screenshot, language_code)
            self.ocr_result.emit(text)
