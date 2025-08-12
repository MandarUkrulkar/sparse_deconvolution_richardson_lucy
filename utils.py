import os
import cv2
import numpy as np

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def load_image_rgb(path):
    """Load an image and ensure it's 3-channel RGB (OpenCV BGR ordering)."""
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    if img.ndim == 2:
        # grayscale -> convert to 3-channel BGR
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        # RGBA -> BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img

def save_image(path, img):
    cv2.imwrite(path, img)

def generate_gaussian_psf(size=7, sigma=2.0):
    """Return a normalized 2D Gaussian PSF (numpy array)."""
    k = cv2.getGaussianKernel(ksize=size, sigma=sigma)
    psf = np.outer(k, k)
    psf = psf.astype(np.float32)
    psf /= psf.sum()
    return psf
