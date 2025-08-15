# Sparse Deconvolution (Richardson–Lucy) — Hematology/histology tile enhancer

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


<?xml version="1.0" encoding="UTF-8"?>
<svg width="900" height="420" xmlns="http://www.w3.org/2000/svg">
  <style>
    .box { fill:#f6f9ff; stroke:#3b82f6; stroke-width:2; rx:8; }
    .txt { font: 14px sans-serif; fill:#0f172a; }
    .title { font: 18px sans-serif; font-weight:bold; }
    .arrow { stroke:#0f172a; stroke-width:2; marker-end:url(#arr); }
  </style>
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="6" refY="3"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L6,3 L0,6 z" fill="#0f172a" />
    </marker>
  </defs>

  <text x="20" y="28" class="title">Algorithm flow — Richardson–Lucy (stabilized)</text>

  <rect x="20" y="50" width="180" height="60" class="box"/>
  <text x="30" y="80" class="txt">1. Load image</text>
  <text x="30" y="98" class="txt">(ensure RGB)</text>

  <rect x="250" y="50" width="200" height="60" class="box"/>
  <text x="260" y="80" class="txt">2. Prepare PSF</text>
  <text x="260" y="98" class="txt">(Gaussian kernel)</text>

  <rect x="520" y="50" width="220" height="60" class="box"/>
  <text x="530" y="80" class="txt">3. Initialize estimate</text>
  <text x="530" y="98" class="txt">(blurred original)</text>

  <line x1="200" y1="80" x2="250" y2="80" class="arrow"/>
  <line x1="450" y1="80" x2="520" y2="80" class="arrow"/>

  <rect x="120" y="150" width="660" height="180" class="box"/>
  <text x="160" y="175" class="txt">Iterative loop (k = 1 .. iterations)</text>

  <text x="140" y="195" class="txt">• convolved = estimated * PSF (spatial conv)</text>
  <text x="140" y="216" class="txt">• ratio = observed / (convolved + ε)</text>
  <text x="140" y="237" class="txt">• correction = smooth( ratio * flipped-PSF )</text>
  <text x="140" y="258" class="txt">• clamp(correction) and update: estimated *= correction</text>

  <line x1="430" y1="230" x2="720" y2="230" class="arrow"/>
  <text x="520" y="210" class="txt">stability: clip, smooth, small updates</text>

  <rect x="280" y="350" width="340" height="50" class="box"/>
  <text x="300" y="380" class="txt">Final: merge color channels → save</text>
</svg>



<?xml version="1.0" encoding="UTF-8"?>
<svg width="900" height="220" xmlns="http://www.w3.org/2000/svg">
  <style>
    .box { fill:#fff7ed; stroke:#f97316; stroke-width:2; rx:8; }
    .txt { font: 13px sans-serif; fill:#1f2937; }
    .title { font: 16px sans-serif; font-weight:bold; }
    .arrow { stroke:#1f2937; stroke-width:2; marker-end:url(#arr); }
  </style>
  <defs>
    <marker id="arr" markerWidth="10" markerHeight="10" refX="6" refY="3"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L6,3 L0,6 z" fill="#1f2937" />
    </marker>
  </defs>

  <text x="20" y="24" class="title">Color handling: per-channel processing</text>

  <rect x="20" y="40" width="170" height="50" class="box"/>
  <text x="30" y="70" class="txt">Load image (H,W,3)</text>

  <rect x="260" y="20" width="140" height="90" class="box"/>
  <text x="270" y="55" class="txt">Split into channels</text>
  <text x="270" y="73" class="txt">(R, G, B)</text>

  <rect x="460" y="20" width="140" height="90" class="box"/>
  <text x="470" y="55" class="txt">Apply deconvolution</text>
  <text x="470" y="73" class="txt">(each channel separately)</text>

  <rect x="700" y="40" width="160" height="50" class="box"/>
  <text x="710" y="70" class="txt">Merge channels → RGB output</text>

  <line x1="190" y1="65" x2="260" y2="65" class="arrow"/>
  <line x1="400" y1="65" x2="460" y2="65" class="arrow"/>
  <line x1="600" y1="65" x2="700" y2="65" class="arrow"/>
</svg>





conda env create -f environment.yml
conda activate sparse_deconv


## Design & intuition (short)

We treat the observed image I as I = S * K + noise, where S is the true image and K the PSF (Gaussian by default). The algorithm:

Initialize estimate S0 (slightly blurred original).

At each iteration:

Re-blur estimate: S_k * K → get convolved

Compute ratio I / (convolved + eps) → correction signal

Smooth correction and clamp updates to avoid instability

Update S_{k+1} = S_k * correction

Process each color channel separately and re-merge.

See diagrams/flow.svg and diagrams/channels.svg for visual explanation.

## Tips & tuning
iterations: 8–20 is usually good. Increase slowly.

psf_sigma: controls assumed blur — larger sigma => stronger deblurring.

Use GPU (--gpu yes or --gpu auto) for large images.

Avoid extremely large iterations (>40) unless you have denoising steps.
