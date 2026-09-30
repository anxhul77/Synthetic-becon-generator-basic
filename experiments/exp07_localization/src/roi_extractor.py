import numpy as np
from dataclasses import dataclass

@dataclass
class ROICrop:
    roi_image: np.ndarray
    xmin: int
    ymin: int
    xmax: int
    ymax: int
    width: int
    height: int
    x_true_full: float
    y_true_full: float
    x_true_roi: float
    y_true_roi: float
    roi_center_x: float
    roi_center_y: float
    crop_offset_x: float
    crop_offset_y: float
    is_out_of_bounds: bool

class ROIExtractor:
    """
    Fixed-size ROI extractor centered on ground-truth beacon position.
    Isolates localization from detection by cropping a spatial region of interest.
    Does NOT pass subpixel ground-truth coordinates into localization algorithms.
    """
    def __init__(self, roi_size: int = 31):
        self.roi_size = int(roi_size)

    def extract_roi(self, image: np.ndarray, x_true: float, y_true: float) -> ROICrop:
        img_h, img_w = image.shape[:2]
        w_roi = self.roi_size
        h_roi = self.roi_size

        cx_int = int(np.round(x_true))
        cy_int = int(np.round(y_true))

        xmin = cx_int - (w_roi // 2)
        ymin = cy_int - (h_roi // 2)
        xmax = xmin + w_roi
        ymax = ymin + h_roi

        is_oob = False
        if xmin < 0 or ymin < 0 or xmax > img_w or ymax > img_h:
            is_oob = True
            # Pad if needed or crop valid region
            pad_left = max(0, -xmin)
            pad_top = max(0, -ymin)
            pad_right = max(0, xmax - img_w)
            pad_bottom = max(0, ymax - img_h)

            valid_xmin = max(0, xmin)
            valid_ymin = max(0, ymin)
            valid_xmax = min(img_w, xmax)
            valid_ymax = min(img_h, ymax)

            sub_img = image[valid_ymin:valid_ymax, valid_xmin:valid_xmax]
            if sub_img.size == 0:
                roi_image = np.zeros((h_roi, w_roi), dtype=np.float64)
            else:
                roi_image = np.pad(sub_img, ((pad_top, pad_bottom), (pad_left, pad_right)), mode='edge')
        else:
            roi_image = image[ymin:ymax, xmin:xmax].copy()

        x_true_roi = x_true - xmin
        y_true_roi = y_true - ymin
        roi_center_x = w_roi / 2.0
        roi_center_y = h_roi / 2.0
        crop_offset_x = x_true_roi - roi_center_x
        crop_offset_y = y_true_roi - roi_center_y

        return ROICrop(
            roi_image=roi_image.astype(np.float64),
            xmin=xmin,
            ymin=ymin,
            xmax=xmax,
            ymax=ymax,
            width=w_roi,
            height=h_roi,
            x_true_full=float(x_true),
            y_true_full=float(y_true),
            x_true_roi=float(x_true_roi),
            y_true_roi=float(y_true_roi),
            roi_center_x=float(roi_center_x),
            roi_center_y=float(roi_center_y),
            crop_offset_x=float(crop_offset_x),
            crop_offset_y=float(crop_offset_y),
            is_out_of_bounds=is_oob
        )

def roi_to_full_coords(x_roi: float, y_roi: float, xmin: int, ymin: int) -> tuple[float, float]:
    """Converts ROI-relative coordinates to full-image coordinates."""
    if x_roi is None or y_roi is None or np.isnan(x_roi) or np.isnan(y_roi):
        return None, None
    return float(x_roi + xmin), float(y_roi + ymin)

def full_to_roi_coords(x_full: float, y_full: float, xmin: int, ymin: int) -> tuple[float, float]:
    """Converts full-image coordinates to ROI-relative coordinates."""
    if x_full is None or y_full is None or np.isnan(x_full) or np.isnan(y_full):
        return None, None
    return float(x_full - xmin), float(y_full - ymin)
