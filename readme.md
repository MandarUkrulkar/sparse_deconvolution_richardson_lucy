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
