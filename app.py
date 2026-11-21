"""
LabClarity AI: Research Microscopy Image Enhancer
Flask Application Backbone & API Controller
"""

import os
import uuid
import json
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

from core.enhancer import MicroscopyEnhancer
from core.metrics import extract_full_metrics_suite
from core.ai_analyzer import MicroscopyAIAnalyzer
from core.synthetic_samples import ensure_samples_directory

# Flask App Initialization
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "labclarity-secret-research-token-2026")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload limit

# Directories configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ENHANCED_FOLDER = os.path.join(BASE_DIR, "enhanced")
SAMPLES_FOLDER = os.path.join(BASE_DIR, "static", "samples")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ENHANCED_FOLDER, exist_ok=True)
os.makedirs(SAMPLES_FOLDER, exist_ok=True)

# Generate synthetic sample library
SAMPLE_REGISTRY = ensure_samples_directory(SAMPLES_FOLDER)

# Initialize Core Engines
enhancer = MicroscopyEnhancer()
ai_analyzer = MicroscopyAIAnalyzer()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff", "bmp", "webp"}

# In-memory storage for active sessions / tasks
ACTIVE_TASKS: Dict[str, Dict[str, Any]] = {}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Renders main interactive laboratory enhancement interface."""
    return render_template(
        "index.html",
        presets=MicroscopyEnhancer.PRESETS,
        samples=list(SAMPLE_REGISTRY.values()),
        disclaimer=MicroscopyAIAnalyzer.NON_DIAGNOSTIC_DISCLAIMER,
    )


@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Retrieve pre-configured microscopy enhancement pipelines."""
    return jsonify({"success": True, "presets": MicroscopyEnhancer.PRESETS})


@app.route("/api/samples", methods=["GET"])
def get_samples():
    """Retrieve available sample microscopy specimens."""
    return jsonify({"success": True, "samples": list(SAMPLE_REGISTRY.values())})


@app.route("/api/load_sample", methods=["POST"])
def load_sample():
    """Load a built-in microscopy sample specimen into an active research session."""
    data = request.get_json() or {}
    sample_id = data.get("sample_id", "fluorescence_hela")

    if sample_id not in SAMPLE_REGISTRY:
        return jsonify({"success": False, "error": f"Sample '{sample_id}' not found."}), 404

    sample_meta = SAMPLE_REGISTRY[sample_id]
    sample_path = sample_meta["path"]

    img = cv2.imread(sample_path)
    if img is None:
        return jsonify({"success": False, "error": "Unable to read sample file."}), 500

    task_id = str(uuid.uuid4())[:8]
    raw_filename = f"sample_{task_id}_{sample_meta['filename']}"
    raw_path = os.path.join(UPLOAD_FOLDER, raw_filename)
    cv2.imwrite(raw_path, img)

    ACTIVE_TASKS[task_id] = {
        "task_id": task_id,
        "original_path": raw_path,
        "original_filename": raw_filename,
        "is_sample": True,
        "sample_meta": sample_meta,
    }

    return jsonify({
        "success": True,
        "task_id": task_id,
        "sample_meta": sample_meta,
        "original_url": f"/api/image/raw/{task_id}",
        "recommended_preset": sample_meta.get("recommended_preset", "fluorescence"),
    })


@app.route("/api/upload", methods=["POST"])
def upload_image():
    """Upload researcher microscopy specimen."""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": f"Invalid file format. Supported extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400

    task_id = str(uuid.uuid4())[:8]
    ext = file.filename.rsplit(".", 1)[1].lower()
    raw_filename = f"upload_{task_id}.{ext}"
    raw_path = os.path.join(UPLOAD_FOLDER, raw_filename)
    file.save(raw_path)

    img = cv2.imread(raw_path)
    if img is None:
        os.remove(raw_path)
        return jsonify({"success": False, "error": "Corrupt or unreadable image file."}), 400

    ACTIVE_TASKS[task_id] = {
        "task_id": task_id,
        "original_path": raw_path,
        "original_filename": raw_filename,
        "is_sample": False,
    }

    return jsonify({
        "success": True,
        "task_id": task_id,
        "original_url": f"/api/image/raw/{task_id}",
        "dimensions": f"{img.shape[1]} x {img.shape[0]}",
    })


@app.route("/api/enhance", methods=["POST"])
def enhance_image():
    """Execute scientific microscopy enhancement pipeline and generate AI research audit."""
    data = request.get_json() or {}
    task_id = data.get("task_id")

    if not task_id or task_id not in ACTIVE_TASKS:
        return jsonify({"success": False, "error": "Invalid or expired task session."}), 400

    session = ACTIVE_TASKS[task_id]
    original_path = session["original_path"]

    img = cv2.imread(original_path)
    if img is None:
        return jsonify({"success": False, "error": "Original specimen image could not be loaded."}), 500

    preset = data.get("preset", "fluorescence")
    denoise_strength = data.get("denoise_strength")
    upscale_factor = data.get("upscale_factor")
    clahe_clip = data.get("clahe_clip")
    sharpness = data.get("sharpness")
    flat_field = data.get("flat_field")

    # Run scientific restoration pipeline
    enhanced_img, applied_config = enhancer.enhance(
        image=img,
        preset=preset,
        denoise_strength=float(denoise_strength) if denoise_strength is not None else None,
        upscale_factor=int(upscale_factor) if upscale_factor is not None else None,
        clahe_clip=float(clahe_clip) if clahe_clip is not None else None,
        sharpness=float(sharpness) if sharpness is not None else None,
        flat_field=bool(flat_field) if flat_field is not None else None,
    )

    # Save enhanced output
    enhanced_filename = f"enhanced_{task_id}.png"
    enhanced_path = os.path.join(ENHANCED_FOLDER, enhanced_filename)
    cv2.imwrite(enhanced_path, enhanced_img)

    # Compute quantitative biophysical metrics
    metrics = extract_full_metrics_suite(img, enhanced_img)

    # Run Generative AI Multimodal Specimen Analysis
    ai_report = ai_analyzer.analyze_enhanced_specimen(
        image=enhanced_img,
        metrics=metrics,
        applied_pipeline=applied_config,
    )

    session["enhanced_path"] = enhanced_path
    session["enhanced_filename"] = enhanced_filename
    session["metrics"] = metrics
    session["pipeline"] = applied_config
    session["ai_report"] = ai_report

    return jsonify({
        "success": True,
        "task_id": task_id,
        "original_url": f"/api/image/raw/{task_id}",
        "enhanced_url": f"/api/image/enhanced/{task_id}",
        "metrics": metrics,
        "pipeline": applied_config,
        "ai_analysis": ai_report,
    })


@app.route("/api/image/raw/<task_id>")
def get_raw_image(task_id):
    """Serve the raw specimen image."""
    if task_id not in ACTIVE_TASKS or "original_path" not in ACTIVE_TASKS[task_id]:
        return "Image not found", 404
    return send_file(ACTIVE_TASKS[task_id]["original_path"], mimetype="image/png")


@app.route("/api/image/enhanced/<task_id>")
def get_enhanced_image(task_id):
    """Serve the restored enhanced specimen image."""
    if task_id not in ACTIVE_TASKS or "enhanced_path" not in ACTIVE_TASKS[task_id]:
        return "Enhanced image not found", 404
    return send_file(ACTIVE_TASKS[task_id]["enhanced_path"], mimetype="image/png")


@app.route("/api/chat", methods=["POST"])
def assistant_chat():
    """Interactive AI microscopy research assistant endpoint."""
    data = request.get_json() or {}
    user_query = data.get("query", "").strip()
    task_id = data.get("task_id")

    if not user_query:
        return jsonify({"success": False, "error": "Query message cannot be empty."}), 400

    context = {}
    if task_id and task_id in ACTIVE_TASKS:
        session = ACTIVE_TASKS[task_id]
        context = {
            "metrics": session.get("metrics", {}),
            "pipeline": session.get("pipeline", {}),
            "modality": session.get("ai_report", {}).get("modality", "Unknown"),
        }

    response_text = ai_analyzer.assistant_chat(user_query=user_query, context=context)

    return jsonify({"success": True, "reply": response_text})


@app.route("/api/export/<format_type>/<task_id>")
def export_results(format_type, task_id):
    """Export enhanced specimen image or laboratory methods report."""
    if task_id not in ACTIVE_TASKS or "enhanced_path" not in ACTIVE_TASKS[task_id]:
        return jsonify({"error": "Task session expired or missing."}), 404

    session = ACTIVE_TASKS[task_id]
    enhanced_path = session["enhanced_path"]

    if format_type == "png":
        return send_file(
            enhanced_path,
            as_attachment=True,
            download_name=f"LabClarity_Enhanced_{task_id}.png",
            mimetype="image/png",
        )

    elif format_type == "tiff":
        tiff_filename = f"LabClarity_Enhanced_{task_id}.tiff"
        tiff_path = os.path.join(ENHANCED_FOLDER, tiff_filename)
        img = cv2.imread(enhanced_path)
        cv2.imwrite(tiff_path, img)
        return send_file(
            tiff_path,
            as_attachment=True,
            download_name=tiff_filename,
            mimetype="image/tiff",
        )

    elif format_type == "report_json":
        report_data = {
            "project": "LabClarity AI: Research Microscopy Image Enhancer",
            "session_id": task_id,
            "disclaimer": MicroscopyAIAnalyzer.NON_DIAGNOSTIC_DISCLAIMER,
            "metrics": session.get("metrics", {}),
            "pipeline_applied": session.get("pipeline", {}),
            "ai_analysis": session.get("ai_report", {}),
        }
        json_path = os.path.join(ENHANCED_FOLDER, f"LabClarity_Report_{task_id}.json")
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=2)
        return send_file(
            json_path,
            as_attachment=True,
            download_name=f"LabClarity_Report_{task_id}.json",
            mimetype="application/json",
        )

    elif format_type == "report_md":
        ai = session.get("ai_report", {})
        m = session.get("metrics", {})
        md_content = f"""# LabClarity AI - Laboratory Microscopy Research Report
**Session ID:** `{task_id}`  
**Classification:** {ai.get('modality', 'Research Microscopy')}  
**Specimen Type:** {ai.get('specimen_classification', 'Laboratory biological sample')}  
**Stain Profile:** {ai.get('staining_fluorophore_profile', 'N/A')}  

---

## Non-Diagnostic Compliance Notice
> **Notice:** {MicroscopyAIAnalyzer.NON_DIAGNOSTIC_DISCLAIMER}

---

## 1. Quantitative Restoration Metrics
| Metric | Original | Enhanced | Delta / Score |
|---|---|---|---|
| **PSNR** | - | - | `{m.get('psnr_db', 'N/A')} dB` |
| **SNR** | - | - | `{m.get('snr_db', 'N/A')} dB` |
| **SSIM** | - | - | `{m.get('ssim', 'N/A')}` |
| **Tenengrad Sharpness** | `{m.get('original_sharpness', 'N/A')}` | `{m.get('enhanced_sharpness', 'N/A')}` | `+{m.get('sharpness_gain_percent', 'N/A')}%` |
| **Shannon Entropy** | `{m.get('original_entropy', 'N/A')} bpp` | `{m.get('enhanced_entropy', 'N/A')} bpp` | Detail Preserved |
| **Resolution** | `{m.get('resolution_original', 'N/A')}` | `{m.get('resolution_enhanced', 'N/A')}` | Upscaled |

---

## 2. Artifact Diagnosis & Optical Physics
{ai.get('artifact_diagnosis', 'N/A')}

## 3. Cellular Morphological Observations
{ai.get('morphological_features', 'N/A')}

## 4. Materials & Methods (Reproducible Laboratory Protocol)
{ai.get('laboratory_methods_protocol', 'N/A')}

---

*Report automatically compiled by LabClarity AI (Team 4) - Pharma & Life Sciences*
"""
        md_path = os.path.join(ENHANCED_FOLDER, f"LabClarity_Report_{task_id}.md")
        with open(md_path, "w") as f:
            f.write(md_content)
        return send_file(
            md_path,
            as_attachment=True,
            download_name=f"LabClarity_Report_{task_id}.md",
            mimetype="text/markdown",
        )

    return jsonify({"error": f"Unsupported export format '{format_type}'."}), 400


@app.route("/api/health")
def health_check():
    """Health verification endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "LabClarity AI: Research Microscopy Image Enhancer",
        "version": "1.0.0",
        "team": "Team 4",
        "domain": "Pharma & Life Sciences",
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "127.0.0.1")
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f"==================================================")
    print(f" LabClarity AI Server launching at http://{host}:{port}")
    print(f"==================================================")
    app.run(host=host, port=port, debug=debug)
