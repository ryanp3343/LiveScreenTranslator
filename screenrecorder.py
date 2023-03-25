import time
import threading
from queue import Queue
from mss import mss
from PIL import Image, ImageChops, ImageOps
import pytesseract

def capture_screenshot():
    with mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.rgb)

def downscale_image(image, scale_factor=0.5):
    width, height = image.size
    new_width, new_height = int(width * scale_factor), int(height * scale_factor)
    return image.resize((new_width, new_height), Image.ANTIALIAS)

def ocr_screenshot(image):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    return pytesseract.image_to_string(image)

def has_changed(prev_screenshot, new_screenshot, threshold=5):
    diff = ImageChops.difference(prev_screenshot, new_screenshot)
    extrema = diff.getextrema()
    max_diff = extrema[1] if isinstance(extrema[0], int) else extrema[0][1]
    return diff.getbbox() is not None and max_diff > threshold

def process_screenshots(queue):
    while True:
        screenshot = queue.get()
        text = ocr_screenshot(screenshot)
        print("OCR Result:")
        print(text)

def main():
    capture_interval = 1  

    screenshot_queue = Queue()
    num_threads = 4 
    for _ in range(num_threads):
        processing_thread = threading.Thread(target=process_screenshots, args=(screenshot_queue,))
        processing_thread.daemon = True
        processing_thread.start()

    prev_screenshot = capture_screenshot().convert("L")  
    prev_screenshot = downscale_image(prev_screenshot)   

    while True:
        time.sleep(capture_interval)
        new_screenshot = capture_screenshot().convert("L")  
        new_screenshot = downscale_image(new_screenshot)   

        if has_changed(prev_screenshot, new_screenshot):
            prev_screenshot = new_screenshot
            screenshot_queue.put(new_screenshot)

if __name__ == '__main__':
    main()
