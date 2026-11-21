"""
Unit Tests for Scientific Microscopy Enhancement Engine and Metrics
"""

import numpy as np
import pytest
from core.enhancer import MicroscopyEnhancer
from core.metrics import (
    compute_psnr,
    compute_snr,
    compute_ssim,
    compute_sharpness,
    compute_entropy,
    extract_full_metrics_suite,
)
from core.synthetic_samples import (
    generate_fluorescence_sample,
    generate_histology_sample,
    generate_phase_contrast_sample,
)


def test_synthetic_sample_generators():
    """Verify synthetic samples generate valid 3-channel 8-bit images."""
    f_sample = generate_fluorescence_sample(128, 128)
    assert f_sample.shape == (128, 128, 3)
    assert f_sample.dtype == np.uint8

    h_sample = generate_histology_sample(128, 128)
    assert h_sample.shape == (128, 128, 3)
    assert h_sample.dtype == np.uint8

    p_sample = generate_phase_contrast_sample(128, 128)
    assert p_sample.shape == (128, 128, 3)
    assert p_sample.dtype == np.uint8


def test_anscombe_invertibility():
    """Verify Anscombe forward and inverse transform round-trip accuracy."""
    enhancer = MicroscopyEnhancer()
    test_data = np.array([[10, 50, 100], [150, 200, 240]], dtype=np.uint8)
    forward = enhancer.anscombe_transform(test_data)
    inverse = enhancer.inverse_anscombe_transform(forward)

    # Allow slight integer discretization error (<= 1 LSB)
    diff = np.abs(test_data.astype(int) - inverse.astype(int))
    assert np.max(diff) <= 2


def test_enhancement_pipeline_execution():
    """Test full enhancement pipeline across all preset configurations."""
    enhancer = MicroscopyEnhancer()
    sample = generate_fluorescence_sample(128, 128)

    # Test each preset
    for preset_key in enhancer.PRESETS.keys():
        enhanced, config = enhancer.enhance(sample, preset=preset_key)
        assert enhanced is not None
        assert enhanced.dtype == np.uint8
        assert len(config["pipeline_steps"]) > 0

        # Check resolution matches upscale factor
        scale = config["upscale_factor"]
        assert enhanced.shape[0] == sample.shape[0] * scale
        assert enhanced.shape[1] == sample.shape[1] * scale


def test_metrics_suite_extraction():
    """Test quantitative biophysical metric calculations."""
    sample = generate_fluorescence_sample(128, 128)
    enhancer = MicroscopyEnhancer()
    enhanced, _ = enhancer.enhance(sample, preset="fluorescence")

    metrics = extract_full_metrics_suite(sample, enhanced)
    assert "psnr_db" in metrics
    assert "snr_db" in metrics
    assert "ssim" in metrics
    assert "sharpness_gain_percent" in metrics
    assert "original_entropy" in metrics
    assert "enhanced_entropy" in metrics

    # Sanity checks
    assert metrics["psnr_db"] > 10.0
    assert 0.0 <= metrics["ssim"] <= 1.0
