import time

class PerformanceTimer:
    """Utility to measure execution time per frame / batch."""
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000.0
        self.fps = 1000.0 / self.elapsed_ms if self.elapsed_ms > 0 else 0.0
