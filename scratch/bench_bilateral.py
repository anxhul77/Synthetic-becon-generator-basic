import time
import numpy as np
import cv2

img = np.random.randint(0, 256, (1080, 1920), dtype=np.uint8)

t0 = time.perf_counter()
res = cv2.bilateralFilter(img, 5, 30.0, 2.0)
t1 = time.perf_counter()

print(f"Bilateral filter 1 frame time: {(t1-t0)*1000:.2f} ms")
