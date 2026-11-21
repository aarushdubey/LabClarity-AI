"""
LabClarity AI: Synthetic Scientific Microscopy Specimen Generator
Generates realistic research microscopy test images with biophysical noise models
(Fluorescence DAPI/GFP HeLa cells, Brightfield Histology H&E, Phase Contrast live culture).
"""

import os
import numpy as np
import cv2


def generate_fluorescence_sample(width: int = 512, height: int = 512) -> np.ndarray:
    """
    Generate synthetic multi-channel fluorescence microscopy image:
    - Blue channel: DAPI-stained cellular nuclei
    - Green channel: GFP-labeled microtubule filaments
    - Noise model: Poisson shot noise (low photon count in low-exposure live cell imaging)
    """
    np.random.seed(42)
    img = np.zeros((height, width, 3), dtype=np.float32)

    # 1. Background dark current / auto-fluorescence
    img[:, :, :] = 12.0 + np.random.normal(0, 2.0, (height, width, 3))

    # 2. Cell nuclei (DAPI - Blue Channel, with some Green bleed-through)
    num_nuclei = 16
    for _ in range(num_nuclei):
        cx = np.random.randint(40, width - 40)
        cy = np.random.randint(40, height - 40)
        axes = (np.random.randint(18, 35), np.random.randint(14, 25))
        angle = np.random.randint(0, 180)

        # Draw smooth Gaussian elliptical nucleus
        nucleus_mask = np.zeros((height, width), dtype=np.float32)
        cv2.ellipse(nucleus_mask, (cx, cy), axes, angle, 0, 360, 1.0, -1)
        nucleus_smooth = cv2.GaussianBlur(nucleus_mask, (15, 15), 5.0)

        # Chromatin condensation spots inside nucleus
        for _ in range(np.random.randint(3, 7)):
            spot_x = int(cx + np.random.normal(0, axes[0] / 3))
            spot_y = int(cy + np.random.normal(0, axes[1] / 3))
            if 0 <= spot_x < width and 0 <= spot_y < height:
                cv2.circle(nucleus_smooth, (spot_x, spot_y), np.random.randint(2, 5), 1.5, -1)

        img[:, :, 0] += nucleus_smooth * 180.0  # Blue
        img[:, :, 1] += nucleus_smooth * 25.0   # Slight green fluorophore bleed

    # 3. Microtubule filaments / cytoskeleton (GFP - Green Channel)
    green_plane = np.zeros((height, width), dtype=np.float32)
    num_filaments = 35
    for _ in range(num_filaments):
        pt1 = (int(np.random.randint(20, width - 20)), int(np.random.randint(20, height - 20)))
        pt2 = (int(np.clip(pt1[0] + np.random.randint(-80, 80), 0, width - 1)), int(np.clip(pt1[1] + np.random.randint(-80, 80), 0, height - 1)))
        cv2.line(green_plane, pt1, pt2, float(np.random.randint(70, 140)), thickness=int(np.random.randint(1, 3)))

    green_plane = cv2.GaussianBlur(green_plane, (5, 5), 1.2)
    img[:, :, 1] += green_plane

    # 4. Realistic Poisson Shot Noise simulation
    # In fluorescence imaging, photon arrival follows a Poisson distribution
    photon_scale = 0.4  # Simulates low-light exposure
    scaled = np.maximum(img * photon_scale, 0)
    poisson_noisy = np.random.poisson(scaled).astype(np.float32) / photon_scale

    # 5. Add CMOS/CCD read noise (Gaussian)
    read_noise = np.random.normal(0, 6.0, (height, width, 3))
    final = np.clip(poisson_noisy + read_noise, 0, 255).astype(np.uint8)
    return final


def generate_histology_sample(width: int = 512, height: int = 512) -> np.ndarray:
    """
    Generate synthetic Brightfield Histology specimen (Hematoxylin & Eosin / H&E stain):
    - Pink/Magenta: Eosin stained cytoplasm & extracellular matrix
    - Deep Purple/Blue: Hematoxylin stained nuclei
    - Artifacts: Optical diffraction blur and subtle illumination fall-off
    """
    np.random.seed(101)
    # Brightfield white background with subtle illumination vignette
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    xx, yy = np.meshgrid(x, y)
    vignette = 1.0 - 0.22 * (xx ** 2 + yy ** 2)

    bg_color = np.array([235, 230, 245], dtype=np.float32)  # Light pinkish-white background
    img = np.tile(bg_color, (height, width, 1)) * vignette[:, :, None]

    # Stroma / Cytoplasm clusters (Eosin - Pink/Magenta BGR: [180, 100, 220])
    for _ in range(12):
        cx = np.random.randint(60, width - 60)
        cy = np.random.randint(60, height - 60)
        r = np.random.randint(40, 90)
        mask = np.zeros((height, width), dtype=np.float32)
        cv2.circle(mask, (cx, cy), r, 1.0, -1)
        mask = cv2.GaussianBlur(mask, (41, 41), 18.0)
        eosin_color = np.array([160, 90, 215], dtype=np.float32)
        img = img * (1.0 - mask[:, :, None] * 0.45) + (eosin_color * mask[:, :, None] * 0.45)

    # Cellular nuclei (Hematoxylin - Deep Purple BGR: [110, 40, 70])
    num_nuclei = 40
    for _ in range(num_nuclei):
        cx = np.random.randint(30, width - 30)
        cy = np.random.randint(30, height - 30)
        axes = (np.random.randint(6, 14), np.random.randint(5, 11))
        angle = np.random.randint(0, 180)
        mask = np.zeros((height, width), dtype=np.float32)
        cv2.ellipse(mask, (cx, cy), axes, angle, 0, 360, 1.0, -1)
        mask = cv2.GaussianBlur(mask, (7, 7), 1.5)
        hematoxylin_color = np.array([95, 30, 65], dtype=np.float32)
        img = img * (1.0 - mask[:, :, None] * 0.75) + (hematoxylin_color * mask[:, :, None] * 0.75)

    # Add optical blur (numerical aperture diffraction limit)
    blurred = cv2.GaussianBlur(img, (7, 7), 2.2)

    # Add sensor noise
    sensor_noise = np.random.normal(0, 5.0, (height, width, 3))
    final = np.clip(blurred + sensor_noise, 0, 255).astype(np.uint8)
    return final


def generate_phase_contrast_sample(width: int = 512, height: int = 512) -> np.ndarray:
    """
    Generate synthetic Phase Contrast microscopy specimen:
    - Neutral mid-gray background
    - Characteristic bright diffraction halo surrounding dark cellular phase objects
    - Low-light granular shot noise
    """
    np.random.seed(202)
    base_gray = 135.0
    img = np.full((height, width), base_gray, dtype=np.float32)

    # Add live adherent cells with phase halos
    num_cells = 18
    for _ in range(num_cells):
        cx = np.random.randint(40, width - 40)
        cy = np.random.randint(40, height - 40)
        axes = (np.random.randint(25, 55), np.random.randint(15, 30))
        angle = np.random.randint(0, 180)

        # Bright halo around border
        halo_mask = np.zeros((height, width), dtype=np.float32)
        cv2.ellipse(halo_mask, (cx, cy), (axes[0] + 8, axes[1] + 8), angle, 0, 360, 1.0, 4)
        halo_smooth = cv2.GaussianBlur(halo_mask, (15, 15), 3.5)
        img += halo_smooth * 55.0

        # Dark cell interior
        cell_mask = np.zeros((height, width), dtype=np.float32)
        cv2.ellipse(cell_mask, (cx, cy), axes, angle, 0, 360, 1.0, -1)
        cell_smooth = cv2.GaussianBlur(cell_mask, (11, 11), 2.5)
        img -= cell_smooth * 45.0

        # Refractive intracellular vesicle/nucleolus
        vx = int(cx + np.random.normal(0, 4))
        vy = int(cy + np.random.normal(0, 4))
        if 0 <= vx < width and 0 <= vy < height:
            cv2.circle(img, (vx, vy), 3, base_gray + 30.0, -1)

    # Convert to 3-channel BGR for uniformity
    img_bgr = np.repeat(img[:, :, None], 3, axis=2)

    # Add Gaussian + uniform sensor thermal noise
    thermal_noise = np.random.normal(0, 7.5, (height, width, 3))
    final = np.clip(img_bgr + thermal_noise, 0, 255).astype(np.uint8)
    return final


def ensure_samples_directory(output_dir: str):
    """
    Generate and save sample microscopy images if they don't exist yet.
    """
    os.makedirs(output_dir, exist_ok=True)
    samples = {
        "fluorescence_hela.png": generate_fluorescence_sample,
        "histology_he.png": generate_histology_sample,
        "phase_contrast_culture.png": generate_phase_contrast_sample,
    }

    metadata = {
        "fluorescence_hela.png": {
            "id": "fluorescence_hela",
            "title": "Fluorescence Microscopy (HeLa DAPI/GFP)",
            "description": "Cultured HeLa cells with DAPI nuclear counterstain and GFP tubulin filaments. Degraded by Poisson low-photon shot noise and photobleaching.",
            "recommended_preset": "fluorescence",
            "modality": "Fluorescence",
        },
        "histology_he.png": {
            "id": "histology_he",
            "title": "Brightfield Histology (H&E Stained Section)",
            "description": "Epithelial tissue biopsy section stained with Hematoxylin & Eosin. Suffering from numerical aperture diffraction blur and illumination gradient.",
            "recommended_preset": "histology_2x",
            "modality": "Brightfield",
        },
        "phase_contrast_culture.png": {
            "id": "phase_contrast_culture",
            "title": "Phase Contrast Live-Cell Monolayer",
            "description": "Unstained primary cell culture showing diffraction ring halos, sensor thermal noise, and low intrinsic contrast.",
            "recommended_preset": "phase_contrast",
            "modality": "Phase Contrast",
        },
    }

    paths = {}
    for filename, generator in samples.items():
        filepath = os.path.join(output_dir, filename)
        if not os.path.exists(filepath):
            img = generator()
            cv2.imwrite(filepath, img)
        meta = metadata[filename].copy()
        meta["filename"] = filename
        meta["path"] = filepath
        paths[meta["id"]] = meta

    return paths
