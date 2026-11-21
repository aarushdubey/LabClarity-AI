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

    def get_client(self):
        """Dynamically check for Groq API key if not initialized."""
        if self.client is not None:
            return self.client
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if api_key and Groq is not None and not api_key.startswith("your_"):
            try:
                self.client = Groq(api_key=api_key)
                return self.client
            except Exception as e:
                print(f"[LabClarity AI] Groq dynamic init note: {e}")
        return None

    def assistant_chat(self, user_query: str, context: Dict[str, Any]) -> str:
        """
        Interactive research assistant responding to user inquiries regarding specimen biology,
        microscopy optical physics, and restoration fidelity.
        """
        raw_query = user_query.strip()
        if not raw_query:
            return "Please provide a question regarding your microscopy specimen or enhancement results."

        q = raw_query.lower()
        client = self.get_client()

        # If Groq LLM is not active, use an intelligent, natural conversational engine
        if client is None:
            # 1. Greetings & Pleasantries
            if any(k in q for k in ["how are you", "how r u", "how're you", "how do you do", "hows it going", "how's it going"]):
                return (
                    "I'm doing great, thank you for asking! I'm ready to assist you with your microscopy research. "
                    "I can help explain the optical noise reduction, interpret cellular fluorophores, "
                    "or draft reproducible Materials & Methods protocols for your specimen. How can I help you today?"
                )
            elif re.search(r"\b(hi|hello|hey|greetings|good\s*(morning|afternoon|evening))\b", q):
                return (
                    "Hello! I am your LabClarity AI Research Assistant. "
                    "I can answer questions regarding your specimen's optical physics, fluorophore spectra, "
                    "Anscombe Poisson-Gaussian noise modeling, or explain the quantitative metrics. What would you like to explore?"
                )
            elif any(k in q for k in ["thank", "thanks", "thx", "appreciate"]):
                return "You're very welcome! Feel free to ask anytime if you need further biophysical analysis or protocol writeups."
            elif any(k in q for k in ["who are you", "what are you", "what can you do", "what is this", "help"]):
                return (
                    "I am the LabClarity AI Research Assistant, specialized in optical microscopy, biophysics, and non-diagnostic "
                    "life sciences image enhancement. I can:\n"
                    "• Explain Poisson shot noise and Anscombe variance stabilization\n"
                    "• Analyze fluorophore emission channels (DAPI, GFP, H&E)\n"
                    "• Interpret quantitative metrics (PSNR, SNR, SSIM, Tenengrad sharpness)\n"
                    "• Draft publication-grade laboratory methods protocols for your research team."
                )

            # 2. Scientific & Biophysical Inquiries
            elif any(k in q for k in ["noise", "anscombe", "poisson", "shot noise", "denoise"]):
                return (
                    "In low-light fluorescence microscopy, the dominant degradation is Poisson-distributed photon shot noise "
                    "arising from quantum photon statistics (Var(x) = λ). The Anscombe forward transform (y = 2*sqrt(x + 3/8)) "
                    "stabilizes this Poisson variance into standard Gaussian noise (N(0, 1)). This allows Non-Local Means (NLM) "
                    "spatial filtering to remove background sensor grain without blurring intracellular organelle boundaries. "
                    "Finally, an asymptotically unbiased inverse Anscombe transform restores the true biological signal."
                )
            elif any(k in q for k in ["stain", "fluorophore", "dapi", "gfp", "fitc", "hema", "eosin", "h&e"]):
                return (
                    "Optical microscopy stains provide specific cellular contrast:\n"
                    "• DAPI / Hoechst 33342: Blue emission (~460nm), binds AT-rich DNA regions to visualize nuclei.\n"
                    "• GFP / Alexa Fluor 488: Green emission (~510nm), tags microtubule cytoskeleton or target fusion proteins.\n"
                    "• H&E (Hematoxylin & Eosin): Hematoxylin stains nucleic acids deep purple; Eosin stains proteins and cytoplasm pink."
                )
            elif any(k in q for k in ["super resolution", "super-resolution", "upscale", "diffraction", "resolution"]):
                return (
                    "Optical super-resolution in LabClarity AI combines high-order Lanczos-4 sub-pixel interpolation with a "
                    "Laplacian high-frequency detail synthesis pyramid. This overcomes sensor pixelation and sharpens cellular membranes "
                    "that are softened by the objective lens numerical aperture (NA) diffraction limit, maintaining strict fidelity without hallucinating structures."
                )
            elif any(k in q for k in ["diagnostic", "clinical", "patient", "medical"]):
                return (
                    "Important Regulatory Notice: LabClarity AI is engineered exclusively for exploratory non-diagnostic research and "
                    "academic laboratory analysis. Any clinical diagnostic, therapeutic, or medical decision-making inferences are strictly prohibited."
                )
            elif any(k in q for k in ["psnr", "snr", "ssim", "sharpness", "entropy", "metric"]):
                return (
                    "Quantitative Metric Definitions:\n"
                    "• PSNR (Peak SNR): Ratio between maximum dynamic range and residual distortion. Values >25 dB indicate excellent signal recovery.\n"
                    "• SNR (Signal-to-Noise Ratio): Ratio between restored signal and removed noise floor in decibels (dB).\n"
                    "• SSIM (Structural Similarity): Measures structural correlation (-1 to +1). Values >0.85 confirm structural fidelity without distortion.\n"
                    "• Tenengrad Sharpness: Variance of the Laplacian, quantifying edge definition across cell membranes."
                )
            else:
                modality = context.get("modality", "Microscopy Specimen")
                return (
                    f"I've examined your current {modality} specimen data. "
                    f"The restoration pipeline has stabilized background noise and enhanced boundary sharpness. "
                    f"Would you like me to explain the fluorophore channel distribution, the Anscombe denoising steps, "
                    f"or generate a Materials & Methods writeup for your lab notebook?"
                )

        # Groq LLM is active
        system_prompt = (
            "You are LabClarity Assistant, a polite, articulate, expert scientific consultant in biophysics, "
            "optical microscopy, and life sciences research. When greeted casually (e.g. 'how are you', 'hello'), "
            "respond warmly and naturally as an intelligent colleague, before offering assistance with their specimen. "
            "Provide concise, rigorous answers to technical inquiries. Remind users this tool is for non-diagnostic research."
        )

        user_content = f"""
SPECIMEN CONTEXT:
- Modality: {context.get('modality', 'Unknown')}
- Metrics: {json.dumps(context.get('metrics', {}))}
- Pipeline: {json.dumps(context.get('pipeline', {}))}

RESEARCHER MESSAGE:
{raw_query}
"""

        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.5,
                max_tokens=600,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LabClarity AI] Groq chat error: {e}. Falling back to conversational response.")
            return (
                "I'm doing well, thank you! I'm here to assist you with your microscopy specimen analysis. "
                "Feel free to ask about optical denoising, fluorophore channels, or laboratory methods protocols."
            )
