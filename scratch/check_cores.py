import os
import cv2

print(f"CPU count: {os.cpu_count()}")
print(f"OpenCV threads: {cv2.getNumThreads()}")
