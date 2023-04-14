#import cv2
#import numpy as np
#from PIL import ImageFilter

#post processing functions if needed
# def increase_contrast(image, alpha=1.5, beta=20):
#     new_image = np.zeros(image.shape, image.dtype)
#     new_image = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
#     return new_image

# def apply_gaussian_blur(image, kernel_size=(5, 5)):
#     blurred_image = cv2.GaussianBlur(image, kernel_size, 0)
#     return blurred_image

# def deskew_image(image):
#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#     thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
#     coords = np.column_stack(np.where(thresh > 0))
#     angle = cv2.minAreaRect(coords)[-1]
    
#     if angle < -45:
#         angle = -(90 + angle)
#     else:
#         angle = -angle

#     (h, w) = image.shape[:2]
#     center = (w // 2, h // 2)
#     M = cv2.getRotationMatrix2D(center, angle, 1.0)
#     deskewed_image = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
#     return deskewed_image

# def downscale_image(image, scale_factor=0.5):
#     width, height = image.size
#     new_width, new_height = int(width * scale_factor), int(height * scale_factor)
#     return image.resize((new_width, new_height), Image.ANTIALIAS)

# def binarize_image(image, block_size=15, offset=5):
#     return image.filter(ImageFilter.UnsharpMask).convert('1', dither=Image.NONE)