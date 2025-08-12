#!/usr/bin/env python3
"""
Main application for stabilized Richardson-Lucy deconvolution with color handling and optional GPU.
"""
import argparse
import os
import sys
from tqdm import tqdm

import numpy as np
import cv2
from scipy.ndimage import gaussian_filter

# Try import cupy (GPU). If not present, we'll fallback to numpy.
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except Exception:
    cp = None
    CUPY_AVAILABLE = False

from utils import ensure_dir, load_image_rgb, save_image, generate_gaussian_psf

def get_backend(use_gpu):
    if use_gpu and CUPY_AVAILABLE:
        return cp
    return np

def to_backend(arr, backend):
    if backend is cp:
        return cp.asarray(arr)
    return arr

def to_numpy(arr, backend):
    if backend is cp:
        return cp.asnumpy(arr)
    return arr

def stable_filter2D(img, kernel, backend):
    """Perform 2D filtering compatible with numpy or cupy (use OpenCV for numpy)."""
    if backend is np:
        return cv2.filter2D(img, -1, kernel)
    else:
        # For cupy: do filtering in frequency domain (safe, kernel small)
        # move kernel and image to GPU (they should already be)
        img_fft = backend.fft.fft2(img)
        pad = (img.shape[0] - kernel.shape[0], img.shape[1] - kernel.shape[1])
        # create kernel padded to image size
        k = backend.zeros(img.shape, dtype=kernel.dtype)
        k[:kernel.shape[0], :kernel.shape[1]] = kernel
        k = backend.roll(k, -kernel.shape[0]//2, axis=0)
        k = backend.roll(k, -kernel.shape[1]//2, axis=1)
        k_fft = backend.fft.fft2(k)
        out = backend.fft.ifft2(img_fft * k_fft).real
        return out

def richardson_lucy_channel(channel, psf, iterations, backend, eps=1e-6,
                            clip_low=0.7, clip_high=1.3, smooth_sigma=1.0):
    """
    Single-channel stabilized Richardson-Lucy implemented in spatial domain (with safe filtering)
    channel: backend array (float)
    psf: numpy array (small)
    """
    # Ensure psf is backend array
    psf_b = to_backend(psf, backend)
    # initial estimate: small gaussian blur to suppress noise
    if backend is np:
        estimated = gaussian_filter(channel, sigma=1.0)
    else:
        # for cupy, use a simple gaussian via convolution with psf
        estimated = channel.copy()
        # tiny gaussian to smooth initial estimate
        estimated = stable_filter2D(estimated, psf_b, backend)

    for i in range(iterations):
        convolved = stable_filter2D(estimated, psf_b, backend)
        convolved = backend.clip(convolved, eps, None)
        ratio = channel / convolved
        # clamp ratio to reduce extreme updates
        ratio = backend.clip(ratio, 0.5, 2.0)
        # compute correction (smoothed)
        correction = stable_filter2D(ratio, psf_b[::-1, ::-1], backend)
        if backend is np:
            correction = gaussian_filter(correction, sigma=smooth_sigma)
        else:
            # simple smoothing: apply psf again
            correction = stable_filter2D(correction, psf_b, backend)
        correction = backend.clip(correction, clip_low, clip_high)
        estimated = estimated * correction
    return estimated

def process_image_file(path, out_path, psf, iterations, backend, verbose=False):
    img = load_image_rgb(path)  # BGR uint8
    # convert BGR->RGB for nicer conceptual mapping (we will save BGR again)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    channels = cv2.split(img_rgb)
    restored = []
    # Ensure channels are backend arrays
    for ch in channels:
        ch_b = to_backend(ch, backend)
        out_ch = richardson_lucy_channel(ch_b, psf, iterations, backend)
        out_ch = to_numpy(out_ch, backend)
        out_ch = np.clip(out_ch * 255.0, 0, 255).astype(np.uint8)
        restored.append(out_ch)
    merged_rgb = cv2.merge(restored)
    merged_bgr = cv2.cvtColor(merged_rgb, cv2.COLOR_RGB2BGR)
    save_image(out_path, merged_bgr)
    if verbose:
        print(f"Saved: {out_path}")

def parse_args():
    p = argparse.ArgumentParser(description="Stabilized Richardson-Lucy Deconvolution (color, GPU optional).")
    p.add_argument("--input_dir", required=True, help="Input directory containing images")
    p.add_argument("--output_dir", required=True, help="Output directory to save processed images")
    p.add_argument("--iterations", type=int, default=10, help="Number of RL iterations (default:10)")
    p.add_argument("--psf_size", type=int, default=7, help="PSF kernel size (odd integer, default:7)")
    p.add_argument("--psf_sigma", type=float, default=2.0, help="PSF Gaussian sigma (default:2.0)")
    p.add_argument("--gpu", choices=("yes","no","auto"), default="auto", help="Use GPU: yes, no, or auto (default:auto)")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()

def main():
    args = parse_args()
    use_gpu = False
    if args.gpu == "yes":
        use_gpu = True
    elif args.gpu == "auto":
        use_gpu = CUPY_AVAILABLE
    else:
        use_gpu = False

    backend = get_backend(use_gpu)

    if use_gpu and not CUPY_AVAILABLE:
        print("Warning: GPU requested but CuPy not available. Falling back to CPU.")
        backend = np

    ensure_dir(args.output_dir)
    psf = generate_gaussian_psf(size=args.psf_size, sigma=args.psf_sigma).astype(np.float32)

    # list images
    files = [f for f in os.listdir(args.input_dir) if f.lower().endswith(('.jpg','.jpeg','.png','.tif','.tiff'))]
    if not files:
        print("No image files found in input_dir.")
        sys.exit(1)

    for fname in tqdm(files, desc="Processing"):
        in_path = os.path.join(args.input_dir, fname)
        out_path = os.path.join(args.output_dir, fname)
        try:
            process_image_file(in_path, out_path, psf, args.iterations, backend, verbose=args.verbose)
        except Exception as e:
            print(f"Error processing {fname}: {e}")

if __name__ == "__main__":
    main()
