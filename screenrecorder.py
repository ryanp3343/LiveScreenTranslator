import time
import threading
from queue import Queue
from mss import mss
from PIL import Image, ImageChops
import pytesseract

def capture_screenshot():
    with mss() as sct:
        monitor = sct.monitors[1]  
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

def ocr_screenshot(image):
    
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    return pytesseract.image_to_string(image)

def has_changed(prev_screenshot, new_screenshot, threshold=5):
    diff = ImageChops.difference(prev_screenshot, new_screenshot)
    return diff.getbbox() is not None and diff.getextrema()[0][1] > threshold

def process_screenshots(queue):
    while True:
        screenshot = queue.get()
        text = ocr_screenshot(screenshot)
        print("OCR Result:")
        print(text)

def main():
    capture_interval = 1  
    
    screenshot_queue = Queue()
    processing_thread = threading.Thread(target=process_screenshots, args=(screenshot_queue,))
    processing_thread.daemon = True
    processing_thread.start()

    prev_screenshot = capture_screenshot()

    while True:
        time.sleep(capture_interval)
        new_screenshot = capture_screenshot()

        if has_changed(prev_screenshot, new_screenshot):
            prev_screenshot = new_screenshot
            screenshot_queue.put(new_screenshot)

if __name__ == '__main__':
    main()
