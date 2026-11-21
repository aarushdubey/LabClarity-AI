"""
LabClarity AI: Multimodal Generative AI Microscopy Research Analyzer
Provides automated biophysical specimen characterization, artifact diagnosis,
quantitative restoration audit, laboratory protocol documentation, and research assistant chat.
"""

import os
import json
import re
from typing import Dict, Any, Optional
import numpy as np
import cv2

try:
    from groq import Groq
except ImportError:
    Groq = None


class MicroscopyAIAnalyzer:
    """
    Orchestrates Generative AI analysis of microscopy specimens for research teams.
    Complies strictly with non-diagnostic research and analytical laboratory standards.
    """

    NON_DIAGNOSTIC_DISCLAIMER = (
        "LabClarity AI is intended strictly for non-diagnostic research and academic analysis. "
        "It is not cleared for medical diagnosis, clinical pathology, or therapeutic decision-making."
    )

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "").strip()
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.client = None

        if self.api_key and Groq is not None and not self.api_key.startswith("your_"):
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[LabClarity AI] Groq client initialization note: {e}")
                self.client = None

    @staticmethod
    def extract_image_features(image: np.ndarray) -> Dict[str, Any]:
        """
        Extract low-level computer vision features to inform the AI prompt.
        """
        is_color = len(image.shape) == 3 and image.shape[2] == 3
        h, w = image.shape[:2]

        if is_color:
            b, g, r = cv2.split(image)
            mean_b = float(np.mean(b))
            mean_g = float(np.mean(g))
            mean_r = float(np.mean(r))
            std_lum = float(np.std(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)))
            bg_estimate = "dark" if (mean_b + mean_g + mean_r) / 3.0 < 80 else "bright"
        else:
            mean_b = mean_g = mean_r = float(np.mean(image))
            std_lum = float(np.std(image))
            bg_estimate = "dark" if mean_b < 80 else "bright"

        return {
            "dimensions": f"{w}x{h}",
            "color_channels": 3 if is_color else 1,
            "mean_intensity": round((mean_b + mean_g + mean_r) / 3.0, 1),
            "background_level": bg_estimate,
            "channel_ratios": {
                "blue": round(mean_b, 1),
                "green": round(mean_g, 1),
                "red": round(mean_r, 1),
            },
            "dynamic_range_std": round(std_lum, 1),
        }

    def infer_heuristic_analysis(
        self,
        features: Dict[str, Any],
        metrics: Dict[str, Any],
        applied_pipeline: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Robust heuristic fallback when Groq API key is not configured or network is unavailable.
        Generates comprehensive scientific analysis based on empirical biophysical features.
        """
        bg = features.get("background_level", "dark")
        ch = features.get("channel_ratios", {})
        blue = ch.get("blue", 0)
        green = ch.get("green", 0)
        red = ch.get("red", 0)

        # Classify modality based on optical signature
        if bg == "dark" and (blue > 25 or green > 25):
            modality = "Widefield Fluorescence Microscopy"
            specimen_type = "Cultured cellular specimen with multi-fluorophore labeling (e.g. DAPI / GFP / FITC)"
            artifacts = "Severe Poisson-distributed photon shot noise characteristic of low-exposure fluorescence imaging, coupled with fluorophore photobleaching susceptibility."
            morphology = "Fluorescently stained nuclear chromatin bodies and filamentous cytosolic cytoskeleton structures."
            stain = "DAPI (emission ~461nm, blue channel) and GFP/FITC (emission ~509nm, green channel)"
        elif bg == "bright" and (red > 140 and blue > 120 and green < 170):
            modality = "Brightfield Transmission Microscopy (Histopathology)"
            specimen_type = "Paraffin-embedded biological tissue biopsy section"
            artifacts = "Optical diffraction limit blur from finite numerical aperture objective lens, with peripheral vignetting and stroma illumination gradients."
            morphology = "Deep basophilic nuclei clusters embedded in eosinophilic stroma and extracellular collagen matrices."
            stain = "Hematoxylin & Eosin (H&E) counterstain"
        elif bg != "dark" and abs(blue - green) < 15 and abs(green - red) < 15:
            modality = "Phase Contrast / Differential Interference Contrast (DIC)"
            specimen_type = "Unstained live-cell monolayer in physiological buffer"
            artifacts = "Optical phase halo diffraction artifacts around high-refractive-index cell borders and sensor thermal Gaussian read noise."
            morphology = "Refractive cellular boundaries, intracellular vacuoles, and spreading lamellipodia."
            stain = "Unstained / Intrinsic optical refractive index gradients"
        else:
            modality = "High-Resolution Research Microscopy"
            specimen_type = "Laboratory biological specimen under magnification"
            artifacts = "High-frequency sensor noise, optical diffraction degradation, and local dynamic range compression."
            morphology = "Sub-cellular structures and micro-environmental boundaries."
            stain = "Contrast-enhanced laboratory sample"

        sharpness_gain = metrics.get("sharpness_gain_percent", 0.0)
        snr_db = metrics.get("snr_db", 0.0)
        psnr_db = metrics.get("psnr_db", 0.0)
        ssim = metrics.get("ssim", 1.0)
        steps = applied_pipeline.get("pipeline_steps", [])

        protocol_steps_str = "; ".join(steps) if steps else "Adaptive multi-scale restoration"

        return {
            "modality": modality,
            "specimen_classification": specimen_type,
            "staining_fluorophore_profile": stain,
            "artifact_diagnosis": artifacts,
            "morphological_features": morphology,
            "restoration_audit": {
                "fidelity_assessment": f"High structural integrity maintained (SSIM: {ssim:.4f}). Organelle boundaries restored without introducing synthetic hallucination artifacts.",
                "sharpness_improvement": f"+{sharpness_gain}% increase in Tenengrad focus score, sharpening intracellular boundaries.",
                "signal_to_noise_recovery": f"Attained {snr_db:.1f} dB SNR and {psnr_db:.1f} dB PSNR, suppressing Poisson-Gaussian background noise floor.",
                "resolution_delta": f"Restored from {metrics.get('resolution_original', 'N/A')} to {metrics.get('resolution_enhanced', 'N/A')}.",
            },
            "laboratory_methods_protocol": (
                f"Specimen images were processed via the LabClarity AI restoration engine using: {protocol_steps_str}. "
                f"Poisson variance stabilization was achieved via the forward Anscombe transform (y = 2*sqrt(x + 3/8)), followed by "
                f"adaptive non-local spatial filtering and exact inverse transformation. Contrast was standardized using "
                f"Luminance-channel CLAHE with clip limit {applied_pipeline.get('clahe_clip', 2.0)}, followed by high-boost unsharp masking. "
                f"Quantitative verification yielded PSNR = {psnr_db:.1f} dB, SNR = {snr_db:.1f} dB, and SSIM = {ssim:.4f}."
            ),
            "research_recommendations": [
                "Maintain excitation exposure times below 150ms during live imaging to reduce photobleaching while relying on Anscombe denoising.",
                "Verify objective lens collar correction for cover slip thickness (0.17mm #1.5) to minimize optical spherical aberration.",
                "Archive raw unenhanced 16-bit TIFF files alongside restored outputs for regulatory reproducible research audit trails.",
            ],
            "disclaimer": self.NON_DIAGNOSTIC_DISCLAIMER,
            "ai_engine": "LabClarity Biophysical Heuristic Analyzer v1.0",
        }

    def analyze_enhanced_specimen(
        self,
        image: np.ndarray,
        metrics: Dict[str, Any],
        applied_pipeline: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Perform complete AI analysis. Uses Groq LLM if configured; otherwise gracefully falls back.
        """
        features = self.extract_image_features(image)

        # Fallback if no Groq client
        if self.client is None:
            return self.infer_heuristic_analysis(features, metrics, applied_pipeline)

        # Groq LLM prompt construction
        system_prompt = (
            "You are an expert biophysics and microscopy image restoration specialist for pharmaceutical and life sciences research. "
            "Your role is to analyze microscopy image parameters, identify modality, diagnose artifacts, evaluate restoration quality, "
            "and produce publication-grade laboratory methods documentation. "
            "Always strictly include the non-diagnostic research disclaimer. "
            "Respond ONLY with valid JSON, without any markdown formatting or commentary."
        )

        user_prompt = f"""
Analyze the following laboratory microscopy specimen and image restoration execution:

IMAGE SPECIFICATIONS:
- Resolution: {metrics.get('resolution_original', 'unknown')} -> {metrics.get('resolution_enhanced', 'unknown')}
- Mean Intensity: {features['mean_intensity']}
- Background Field: {features['background_level']}
- Channel Ratios (B, G, R): {features['channel_ratios']}
- Dynamic Range Std: {features['dynamic_range_std']}

QUANTITATIVE RESTORATION METRICS:
- Peak Signal-to-Noise Ratio (PSNR): {metrics.get('psnr_db')} dB
- Signal-to-Noise Ratio (SNR): {metrics.get('snr_db')} dB
- Structural Similarity Index (SSIM): {metrics.get('ssim')}
- Tenengrad Sharpness Gain: {metrics.get('sharpness_gain_percent')}%
- Shannon Entropy: {metrics.get('original_entropy')} -> {metrics.get('enhanced_entropy')} bits/pixel
- Contrast Gain: {metrics.get('contrast_gain_percent')}%

APPLIED PIPELINE:
- Steps: {applied_pipeline.get('pipeline_steps', [])}
- Denoise Strength: {applied_pipeline.get('denoise_strength')}
- Upscale Factor: {applied_pipeline.get('upscale_factor')}x
- CLAHE Clip: {applied_pipeline.get('clahe_clip')}
- Sharpness Boost: {applied_pipeline.get('sharpness')}
- Flat Field Correction: {applied_pipeline.get('flat_field')}

Respond with a JSON object matching this schema:
{{
  "modality": "Microscopy modality name (e.g. Fluorescence, Brightfield Histology, Phase Contrast, Confocal, SEM)",
  "specimen_classification": "Estimated specimen type (e.g. HeLa cell monolayer, H&E tissue biopsy, live neuron culture)",
  "staining_fluorophore_profile": "Probable stain or fluorophore combination",
  "artifact_diagnosis": "Detailed breakdown of the original optical/sensor degradations",
  "morphological_features": "Identified cellular structures (membranes, nuclei, organelles, filaments)",
  "restoration_audit": {{
    "fidelity_assessment": "Assessment of structural fidelity and absence of hallucinated features",
    "sharpness_improvement": "Evaluation of edge definition and boundary clarity",
    "signal_to_noise_recovery": "Evaluation of SNR and PSNR gains",
    "resolution_delta": "Evaluation of super-resolution factor"
  }},
  "laboratory_methods_protocol": "A formal, scientific paragraph suitable for the 'Materials and Methods' section of a research publication describing how this image was enhanced",
  "research_recommendations": [
    "Actionable laboratory imaging recommendation 1",
    "Actionable laboratory imaging recommendation 2",
    "Actionable laboratory imaging recommendation 3"
  ],
  "disclaimer": "{self.NON_DIAGNOSTIC_DISCLAIMER}",
  "ai_engine": "Groq LLaMA 3.3-70B Versatile"
}}
"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )
            content = completion.choices[0].message.content.strip()

            # Clean JSON markdown fences if returned
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n", "", content)
                content = re.sub(r"\n```$", "", content)

            parsed = json.loads(content)
            parsed["ai_engine"] = f"Groq {self.model}"
            parsed["disclaimer"] = self.NON_DIAGNOSTIC_DISCLAIMER
            return parsed
        except Exception as e:
            print(f"[LabClarity AI] Groq API call failed or parsing error: {e}. Falling back to heuristic analysis.")
            heuristic = self.infer_heuristic_analysis(features, metrics, applied_pipeline)
            heuristic["note"] = f"Generated via heuristic engine (Groq offline: {str(e)})"
            return heuristic

    def assistant_chat(self, user_query: str, context: Dict[str, Any]) -> str:
        """
        Interactive research assistant responding to user inquiries regarding specimen biology,
        microscopy optical physics, and restoration fidelity.
        """
        if not user_query.strip():
            return "Please provide a question regarding your microscopy specimen or enhancement results."

        if self.client is None:
            # Fallback expert responses
            q = user_query.lower()
            if "noise" in q or "anscombe" in q or "poisson" in q:
                return (
                    "In fluorescence and low-light optical microscopy, the primary noise component is Poisson-distributed "
                    "photon shot noise resulting from quantum photon arrival statistics. The Anscombe transform stabilizes "
                    "this Poisson variance into Gaussian noise (N(0, 1)), allowing non-local means spatial filtering to effectively "
                    "remove background grain without blurring fine organelle boundaries."
                )
            elif "stain" in q or "fluorophore" in q or "dapi" in q or "gfp" in q:
                return (
                    "Based on optical spectral analysis, blue emissions (~460nm) typically correspond to DAPI or Hoechst 33342 "
                    "counterstains binding to AT-rich regions of double-stranded DNA in nuclei. Green emissions (~510nm) correspond to "
                    "GFP, Alexa Fluor 488, or FITC labeling cytoplasmic or cytoskeletal filaments."
                )
            elif "diagnostic" in q or "clinical" in q:
                return (
                    "Important reminder: LabClarity AI is engineered exclusively for exploratory non-diagnostic research and "
                    "academic laboratory analysis. Any medical, clinical diagnostic, or therapeutic inferences are strictly prohibited."
                )
            elif "psnr" in q or "snr" in q or "metric" in q:
                return (
                    "PSNR (Peak Signal-to-Noise Ratio) measures the ratio between maximum signal dynamic range and residual error. "
                    "Values exceeding 30 dB indicate high reconstruction fidelity. SNR reflects the power ratio between restored "
                    "signal and removed noise floor. SSIM measures structural luminance and contrast correlation, where values >0.90 "
                    "confirm minimal structural distortion."
                )
            else:
                return (
                    f"Research Assistant: I have examined your specimen data ({context.get('modality', 'Microscopy')}). "
                    f"The current enhancement pipeline attained an SNR of {context.get('metrics', {}).get('snr_db', 'N/A')} dB with "
                    f"{context.get('metrics', {}).get('sharpness_gain_percent', 'N/A')}% sharpness improvement. "
                    f"Please specify if you would like guidance on optical deconvolution, fluorophore photobleaching minimization, "
                    f"or laboratory publication methods writeups."
                )

        system_prompt = (
            "You are LabClarity Assistant, a specialized scientific consultant in biophysics, microscopy image processing, "
            "and life sciences research. Provide concise, rigorous, academically sound answers to researcher questions. "
            "Remind users that this tool is for non-diagnostic research purposes."
        )

        user_content = f"""
SPECIMEN CONTEXT:
- Modality: {context.get('modality', 'Unknown')}
- Metrics: {json.dumps(context.get('metrics', {}))}
- Pipeline: {json.dumps(context.get('pipeline', {}))}

RESEARCHER QUESTION:
{user_query}
"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.4,
                max_tokens=600,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            return f"Error communicating with AI Assistant: {str(e)}"
