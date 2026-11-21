"""
Scientific Quantitative Image Quality Metrics for Research Microscopy
Calculates PSNR, SNR, SSIM, Tenengrad Focus/Sharpness, Shannon Entropy, and Contrast Improvement.
"""

import numpy as np
import cv2


def compute_mse(imageA: np.ndarray, imageB: np.ndarray) -> float:
    """Compute the Mean Squared Error between two images."""
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1] * (imageA.shape[2] if len(imageA.shape) == 3 else 1))
    return float(err)


def compute_psnr(original: np.ndarray, enhanced: np.ndarray) -> float:
    """
    Compute Peak Signal-to-Noise Ratio (PSNR) in dB.
    Higher value indicates higher fidelity to signal.
    """
    # Resize original to enhanced if super-resolution was applied
    if original.shape[:2] != enhanced.shape[:2]:
        original_resized = cv2.resize(original, (enhanced.shape[1], enhanced.shape[0]), interpolation=cv2.INTER_LANCZOS4)
    else:
        original_resized = original

    mse = compute_mse(original_resized, enhanced)
    if mse == 0:
        return 100.0  # Identical images
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return float(round(psnr, 2))


def compute_snr(original: np.ndarray, enhanced: np.ndarray) -> float:
    """
    Compute Signal-to-Noise Ratio (SNR) in decibels (dB) between estimated signal and noise residual.
    """
    if original.shape[:2] != enhanced.shape[:2]:
        original_resized = cv2.resize(original, (enhanced.shape[1], enhanced.shape[0]), interpolation=cv2.INTER_LANCZOS4)
    else:
        original_resized = original

    signal = enhanced.astype(np.float64)
    noise = np.abs(original_resized.astype(np.float64) - signal)
    
    signal_power = np.mean(signal ** 2)
    noise_power = np.mean(noise ** 2)

    if noise_power <= 1e-10:
        return 60.0
    if signal_power <= 1e-10:
        return 0.0

    snr_db = 10 * np.log10(signal_power / noise_power)
    return float(round(snr_db, 2))


def compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Compute Structural Similarity Index (SSIM) between two images.
    Values range from -1 to +1 (1.0 = identical structural fidelity).
    """
    if img1.shape[:2] != img2.shape[:2]:
        img1 = cv2.resize(img1, (img2.shape[1], img2.shape[0]), interpolation=cv2.INTER_LANCZOS4)

    # Convert to grayscale if 3 channels
    if len(img1.shape) == 3:
        g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY).astype(np.float64)
        g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY).astype(np.float64)
    else:
        g1 = img1.astype(np.float64)
        g2 = img2.astype(np.float64)

    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2

    # Gaussian weighting window (11x11, sigma=1.5)
    kernel = cv2.getGaussianKernel(11, 1.5)
    window = np.outer(kernel, kernel.transpose())

    mu1 = cv2.filter2D(g1, -1, window)[5:-5, 5:-5]
    mu2 = cv2.filter2D(g2, -1, window)[5:-5, 5:-5]

    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2

    sigma1_sq = cv2.filter2D(g1 ** 2, -1, window)[5:-5, 5:-5] - mu1_sq
    sigma2_sq = cv2.filter2D(g2 ** 2, -1, window)[5:-5, 5:-5] - mu2_sq
    sigma12 = cv2.filter2D(g1 * g2, -1, window)[5:-5, 5:-5] - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    return float(round(np.mean(ssim_map), 4))


def compute_sharpness(image: np.ndarray) -> float:
    """
    Compute Tenengrad / Laplacian variance focus score.
    Higher values correlate with crisper cellular membrane and organelle boundaries.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    score = float(np.var(laplacian))
    return float(round(score, 2))


def compute_entropy(image: np.ndarray) -> float:
    """
    Compute Shannon Entropy (bits per pixel) measuring information capacity and detail content.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.ravel() / hist.sum()
    non_zero = hist[hist > 0]
    entropy = -np.sum(non_zero * np.log2(non_zero))
    return float(round(entropy, 2))


def compute_contrast(image: np.ndarray) -> float:
    """
    Compute RMS (Root Mean Square) contrast score.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float64)
    else:
        gray = image.astype(np.float64)
    return float(round(np.std(gray), 2))


def extract_full_metrics_suite(original: np.ndarray, enhanced: np.ndarray) -> dict:
    """
    Extract comprehensive before-and-after biophysical image metrics.
    """
    orig_sharpness = compute_sharpness(original)
    enh_sharpness = compute_sharpness(enhanced)
    sharpness_delta_pct = round(((enh_sharpness - orig_sharpness) / (orig_sharpness + 1e-5)) * 100, 1)

    orig_entropy = compute_entropy(original)
    enh_entropy = compute_entropy(enhanced)

    orig_contrast = compute_contrast(original)
    enh_contrast = compute_contrast(enhanced)
    contrast_delta_pct = round(((enh_contrast - orig_contrast) / (orig_contrast + 1e-5)) * 100, 1)

    psnr = compute_psnr(original, enhanced)
    snr = compute_snr(original, enhanced)
    ssim = compute_ssim(original, enhanced)

    return {
        "psnr_db": psnr,
        "snr_db": snr,
        "ssim": ssim,
        "original_sharpness": orig_sharpness,
        "enhanced_sharpness": enh_sharpness,
        "sharpness_gain_percent": sharpness_delta_pct,
        "original_entropy": orig_entropy,
        "enhanced_entropy": enh_entropy,
        "original_contrast": orig_contrast,
        "enhanced_contrast": enh_contrast,
        "contrast_gain_percent": contrast_delta_pct,
        "resolution_original": f"{original.shape[1]} x {original.shape[0]}",
        "resolution_enhanced": f"{enhanced.shape[1]} x {enhanced.shape[0]}",
    }
