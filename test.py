import opencv
import cv2
from pprint import pprint

if __name__ == "__main__":
    img1 =  cv2.imread('1.jpg', 0)
    img2 = cv2.imread('2.jpg', 0)

    diff = opencv.get_image_difference(img1, img2)
    pprint(diff)