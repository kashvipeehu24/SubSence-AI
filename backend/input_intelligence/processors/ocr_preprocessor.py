"""
OCR Preprocessing Filters

Provides a suite of PIL and numpy-based image filters to enhance image quality
and character contrast prior to running text OCR.

Author: SubSense AI Team
"""

from __future__ import annotations

import logging
import numpy as np
from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)


def preprocess_image(img: Image.Image) -> Image.Image:
    """Applies image preprocessing filters to optimize raw images for OCR accuracy.

    Applies: EXIF auto-rotation, grayscale conversion, upscaling, sharpening,
    Otsu threshold binarization, and median denoising filters.

    Args:
        img: A PIL Image object.

    Returns:
        Image.Image: The enhanced PIL Image object.
    """
    try:
        # 1. Correct camera orientation using EXIF metadata
        img = ImageOps.exif_transpose(img)

        # 2. Convert to Grayscale
        if img.mode != "L":
            img = img.convert("L")

        # 3. Resize / Upscale (double the dimensions to help OCR with smaller font details)
        w, h = img.size
        if w < 2000 and h < 2000:
            img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)

        # 4. Sharpen and enhance edges
        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.EDGE_ENHANCE)

        # 5. Otsu's Binarization (adaptive global thresholding)
        arr = np.array(img)
        hist, bin_edges = np.histogram(arr, bins=256, range=(0, 256))
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0

        weight1 = np.cumsum(hist)
        weight2 = np.cumsum(hist[::-1])[::-1]

        mean1 = np.cumsum(hist * bin_centers) / (weight1 + 1e-10)
        mean2 = (np.cumsum((hist * bin_centers)[::-1]) / (weight2[::-1] + 1e-10))[::-1]

        variance12 = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2
        idx = np.argmax(variance12)
        threshold = bin_centers[idx]

        # Keep threshold in safe bounds
        if threshold < 30 or threshold > 220:
            threshold = 127

        bin_arr = np.where(arr > threshold, 255, 0).astype(np.uint8)
        img = Image.fromarray(bin_arr)

        # 6. Denoise using a Median Filter
        img = img.filter(ImageFilter.MedianFilter(size=3))

        logger.info("Image preprocessing filter pipeline completed. Adaptive threshold: %.2f", threshold)
    except Exception as e:
        logger.error("Failed to apply image preprocessing filters: %s. Returning raw image.", str(e))

    return img
