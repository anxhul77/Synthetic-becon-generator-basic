import sys
sys.path.insert(0, ".")
import time
import os
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from generator.camera import PinholeCamera
from generator.generator import SyntheticBeaconGenerator
from processing.detector import ClassicalBeaconDetector
from processing.filters import get_filter

def worker_task(arg):
    snr_db, t, seed = arg
    camera = PinholeCamera(width=1920, height=1080)
    generator = SyntheticBeaconGenerator(camera=camera)
    detector = ClassicalBeaconDetector(threshold=160.0)

    img, gt = generator.generate_frame(x0=960.0, y0=540.0, amplitude=150.0, snr_db=snr_db, seed=seed)
    records = []
    for m in ["none", "gaussian", "median", "bilateral"]:
        fn, p = get_filter(m)
        filt = fn(img, **p)
        det = detector.detect(filt, beacon_gt=(960.0, 540.0))
        records.append(det["detected"])
    return records

if __name__ == "__main__":
    tasks = [(15.0, i, 1000 + i) for i in range(100)]
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(worker_task, tasks))
    t1 = time.perf_counter()
    print(f"Processed 100 trials (400 evaluations) on 8 workers in {t1-t0:.2f} seconds!")
