import cv2
import pytesseract
from PIL import ImageGrab
import numpy as np
from win32api import GetSystemMetrics

width= GetSystemMetrics(0)
height = GetSystemMetrics(1)
# Path to the Tesseract executable file
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


while True: 
    screen = np.array(ImageGrab.grab(bbox=(0,0,width,height)))
    gray = cv2.cvtColor(screen,cv2.COLOR_BGR2GRAY)
    threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    clean = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel, iterations=1)
    text = pytesseract.image_to_string(clean, lang='eng', config='--psm 11')
    print(text)

    # Display the screenshot
    cv2.imshow('screen', screen)

    # Exit if the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Close the windows
cv2.destroyAllWindows()