# Sparse Deconvolution (Richardson–Lucy) — histology tile enhancer

This repository contains a production-ready script to apply (stable) Richardson–Lucy deconvolution to histology tile images with optional GPU acceleration (CuPy). It includes safeguards against instability, per-channel color preservation, and configurable PSF/iterations.

---

## What’s included

- `app.py` — main CLI script (GPU/CPU)
- `utils.py` — utility functions (PSF generation, loading/saving)
- `diagrams/flow.svg` — algorithm flow diagram
- `diagrams/channels.svg` — per-channel processing diagram
- `environment.yml` — conda environment
- `examples/before/` and `examples/after/` — places to store input/output examples

---

## Quick start

1. Clone or create the repo directory and add files (see repo contents).
2. Create and activate conda env:
```bash
conda env create -f environment.yml
conda activate sparse_deconv


**Design & intuition (short)**

We treat the observed image I as I = S * K + noise, where S is the true image and K the PSF (Gaussian by default). The algorithm:

Initialize estimate S0 (slightly blurred original).

At each iteration:

Re-blur estimate: S_k * K → get convolved

Compute ratio I / (convolved + eps) → correction signal

Smooth correction and clamp updates to avoid instability

Update S_{k+1} = S_k * correction

Process each color channel separately and re-merge.

See diagrams/flow.svg and diagrams/channels.svg for visual explanation.

**Tips & tuning**
iterations: 8–20 is usually good. Increase slowly.

psf_sigma: controls assumed blur — larger sigma => stronger deblurring.

Use GPU (--gpu yes or --gpu auto) for large images.

Avoid extremely large iterations (>40) unless you have denoising steps.
