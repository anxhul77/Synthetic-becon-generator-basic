import numpy as np

class PinholeCamera:
    """
    Pinhole camera model with authoritative intrinsics (width, height, fx, fy, cx, cy).
    FOV fields are dynamically computed properties derived from focal lengths and sensor dimensions.
    """
    def __init__(self, width: int = 1920, height: int = 1080,
                 fx: float = 2000.0, fy: float = 2000.0,
                 cx: float = 960.0, cy: float = 540.0,
                 fps: float = 60.0):
        self.width = int(width)
        self.height = int(height)
        self.fx = float(fx)
        self.fy = float(fy)
        self.cx = float(cx)
        self.cy = float(cy)
        self.fps = float(fps)

    @property
    def fov_x_deg(self) -> float:
        """Dynamically derived horizontal FOV in degrees: 2 * atan(width / (2 * fx))."""
        return float(2.0 * np.degrees(np.arctan(self.width / (2.0 * self.fx))))

    @property
    def fov_y_deg(self) -> float:
        """Dynamically derived vertical FOV in degrees: 2 * atan(height / (2 * fy))."""
        return float(2.0 * np.degrees(np.arctan(self.height / (2.0 * self.fy))))

    def pixel_to_angle(self, u: float, v: float) -> tuple[float, float]:
        """
        Convert pixel coordinates (u, v) to angles (theta_x, theta_y) in radians relative to optical axis.
        theta_x = atan((u - cx) / fx)
        theta_y = atan((v - cy) / fy)
        """
        theta_x = np.arctan((u - self.cx) / self.fx)
        theta_y = np.arctan((v - self.cy) / self.fy)
        return float(theta_x), float(theta_y)

    def angle_to_pixel(self, theta_x: float, theta_y: float) -> tuple[float, float]:
        """
        Convert angles (theta_x, theta_y) in radians to pixel coordinates (u, v).
        u = cx + fx * tan(theta_x)
        v = cy + fy * tan(theta_y)
        """
        u = self.cx + self.fx * np.tan(theta_x)
        v = self.cy + self.fy * np.tan(theta_y)
        return float(u), float(v)

    @classmethod
    def from_fov(cls, width: int = 640, height: int = 480,
                 fov_x_deg: float = 4.0, fov_y_deg: float = 3.0,
                 fps: float = 30.0) -> "PinholeCamera":
        """
        Creates PinholeCamera instance from target FOV in degrees and resolution.
        Calculates exact focal lengths: fx = width / (2 * tan(fov_x / 2)).
        """
        fx = float(width / (2.0 * np.tan(np.radians(fov_x_deg / 2.0))))
        fy = float(height / (2.0 * np.tan(np.radians(fov_y_deg / 2.0))))
        cx = float(width / 2.0)
        cy = float(height / 2.0)
        return cls(width=width, height=height, fx=fx, fy=fy, cx=cx, cy=cy, fps=fps)

    def to_dict(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "fx": self.fx,
            "fy": self.fy,
            "cx": self.cx,
            "cy": self.cy,
            "fov_x_deg": self.fov_x_deg,
            "fov_y_deg": self.fov_y_deg,
            "fps": self.fps,
        }
