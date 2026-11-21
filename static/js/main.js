/**
 * LabClarity AI: Research Microscopy Image Enhancer
 * Main Frontend Controller & Interactive Laboratory Workbench
 */

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  const state = {
    taskId: null,
    activePreset: "fluorescence",
    viewMode: "slider", // 'slider' | 'side'
    upscaleFactor: 1,
    isProcessing: false,
    currentMetrics: null,
    currentAiReport: null,
  };

  // DOM Elements
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const filePreviewStrip = document.getElementById("filePreviewStrip");
  const uploadedFileName = document.getElementById("uploadedFileName");
  const btnClearFile = document.getElementById("btnClearFile");

  const sampleCards = document.querySelectorAll(".sample-card");
  const presetOptions = document.querySelectorAll(".preset-option");

  // Calibration Sliders
  const toggleAdvParams = document.getElementById("toggleAdvParams");
  const paramDrawer = document.getElementById("paramDrawer");
  const advChevron = document.getElementById("advChevron");

  const denoiseSlider = document.getElementById("denoiseSlider");
  const valDenoise = document.getElementById("valDenoise");
  const claheSlider = document.getElementById("claheSlider");
  const valClahe = document.getElementById("valClahe");
  const sharpnessSlider = document.getElementById("sharpnessSlider");
  const valSharpness = document.getElementById("valSharpness");
  const upscalePills = document.querySelectorAll("#upscalePills .pill-btn");
  const valUpscale = document.getElementById("valUpscale");
  const flatFieldCheckbox = document.getElementById("flatFieldCheckbox");

  const btnEnhance = document.getElementById("btnEnhance");

  // Comparison Stage
  const emptyState = document.getElementById("emptyState");
  const comparisonWrapper = document.getElementById("comparisonWrapper");
  const sideWrapper = document.getElementById("sideWrapper");
  const rawImage = document.getElementById("rawImage");
  const enhancedImage = document.getElementById("enhancedImage");
  const enhancedLayer = document.getElementById("enhancedLayer");
  const sliderDivider = document.getElementById("sliderDivider");
  const sideRawImage = document.getElementById("sideRawImage");
  const sideEnhancedImage = document.getElementById("sideEnhancedImage");

  // Toolbar
  const btnSliderMode = document.getElementById("btnSliderMode");
  const btnSideMode = document.getElementById("btnSideMode");
  const btnZoomToggle = document.getElementById("btnZoomToggle");

  // Metrics
  const valPsnr = document.getElementById("valPsnr");
  const valSnr = document.getElementById("valSnr");
  const valSsim = document.getElementById("valSsim");
  const valSharpnessMetric = document.getElementById("valSharpnessMetric");
  const subSharpnessGain = document.getElementById("subSharpnessGain");
  const valEntropy = document.getElementById("valEntropy");
  const valResolution = document.getElementById("valResolution");

  // AI Report Elements
  const reportPanel = document.getElementById("reportPanel");
  const aiEngineTag = document.getElementById("aiEngineTag");
  const tagModality = document.getElementById("tagModality");
  const tagSpecimen = document.getElementById("tagSpecimen");
  const tagStain = document.getElementById("tagStain");
  const txtArtifactDiagnosis = document.getElementById("txtArtifactDiagnosis");
  const txtMorphology = document.getElementById("txtMorphology");
  const txtProtocol = document.getElementById("txtProtocol");
  const btnCopyProtocol = document.getElementById("btnCopyProtocol");
  const recList = document.getElementById("recList");

  // Export Buttons
  const btnExportTiff = document.getElementById("btnExportTiff");
  const btnExportPng = document.getElementById("btnExportPng");
  const btnExportMd = document.getElementById("btnExportMd");

  // Chat
  const btnOpenChat = document.getElementById("btnOpenChat");
  const chatModal = document.getElementById("chatModal");
  const btnCloseChat = document.getElementById("btnCloseChat");
  const chatInput = document.getElementById("chatInput");
  const btnSendChat = document.getElementById("btnSendChat");
  const chatMessages = document.getElementById("chatMessages");

  // Toast
  const toast = document.getElementById("toast");
  const toastMsg = document.getElementById("toastMsg");

  // ==========================================
  // Helper: Toast Notifications
  // ==========================================
  function showToast(message) {
    toastMsg.textContent = message;
    toast.classList.remove("hidden");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 3200);
  }

  // ==========================================
  // Preset Values Mapping
  // ==========================================
  const PRESET_MAP = {
    fluorescence: { denoise: 0.65, upscale: 1, clahe: 2.5, sharpness: 0.35, flatField: false },
    histology_2x: { denoise: 0.40, upscale: 2, clahe: 2.0, sharpness: 0.55, flatField: true },
    histology_4x: { denoise: 0.45, upscale: 4, clahe: 2.2, sharpness: 0.65, flatField: true },
    phase_contrast: { denoise: 0.50, upscale: 1, clahe: 3.0, sharpness: 0.60, flatField: true },
    electron_microscopy: { denoise: 0.60, upscale: 2, clahe: 3.5, sharpness: 0.70, flatField: false },
  };

  function applyPresetValues(presetKey) {
    const p = PRESET_MAP[presetKey];
    if (!p) return;

    denoiseSlider.value = p.denoise;
    valDenoise.textContent = p.denoise.toFixed(2);

    claheSlider.value = p.clahe;
    valClahe.textContent = p.clahe.toFixed(1);

    sharpnessSlider.value = p.sharpness;
    valSharpness.textContent = p.sharpness.toFixed(2);

    state.upscaleFactor = p.upscale;
    valUpscale.textContent = `${p.upscale}x`;
    upscalePills.forEach((btn) => {
      btn.classList.toggle("active", parseInt(btn.dataset.val) === p.upscale);
    });

    flatFieldCheckbox.checked = p.flatField;
  }

  // Preset Selection Click
  presetOptions.forEach((opt) => {
    opt.addEventListener("click", () => {
      presetOptions.forEach((o) => o.classList.remove("active"));
      opt.classList.add("active");
      state.activePreset = opt.dataset.preset;
      applyPresetValues(state.activePreset);
      showToast(`Preset: ${opt.querySelector(".preset-name").textContent}`);
    });
  });

  // Accordion Toggle
  toggleAdvParams.addEventListener("click", () => {
    paramDrawer.classList.toggle("collapsed");
    advChevron.classList.toggle("fa-chevron-down");
    advChevron.classList.toggle("fa-chevron-up");
  });

  // Slider Input Listeners
  denoiseSlider.addEventListener("input", (e) => {
    valDenoise.textContent = parseFloat(e.target.value).toFixed(2);
  });

  claheSlider.addEventListener("input", (e) => {
    valClahe.textContent = parseFloat(e.target.value).toFixed(1);
  });

  sharpnessSlider.addEventListener("input", (e) => {
    valSharpness.textContent = parseFloat(e.target.value).toFixed(2);
  });

  upscalePills.forEach((pill) => {
    pill.addEventListener("click", () => {
      upscalePills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state.upscaleFactor = parseInt(pill.dataset.val);
      valUpscale.textContent = `${state.upscaleFactor}x`;
    });
  });

  // ==========================================
  // Sample Specimen Loading
  // ==========================================
  sampleCards.forEach((card) => {
    card.addEventListener("click", async () => {
      sampleCards.forEach((c) => c.classList.remove("active"));
      card.classList.add("active");

      const sampleId = card.dataset.sampleId;
      showToast("Loading research sample...");

      try {
        const res = await fetch("/api/load_sample", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sample_id: sampleId }),
        });
        const data = await res.json();
        if (data.success) {
          state.taskId = data.task_id;

          // Set recommended preset
          if (data.recommended_preset) {
            state.activePreset = data.recommended_preset;
            presetOptions.forEach((opt) => {
              opt.classList.toggle("active", opt.dataset.preset === state.activePreset);
            });
            applyPresetValues(state.activePreset);
          }

          // Display preview on stage
          displayRawSpecimen(data.original_url);
          showToast(`Loaded: ${data.sample_meta.title}`);
        } else {
          showToast(`Error: ${data.error}`);
        }
      } catch (err) {
        showToast("Network error loading specimen sample.");
      }
    });
  });

  // ==========================================
  // File Upload Handlers
  // ==========================================
  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  btnClearFile.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.value = "";
    filePreviewStrip.classList.add("hidden");
    dropZone.querySelector(".drop-zone-prompt").classList.remove("hidden");
  });

  async function handleFileSelected(file) {
    sampleCards.forEach((c) => c.classList.remove("active"));
    uploadedFileName.textContent = file.name;
    filePreviewStrip.classList.remove("hidden");
    dropZone.querySelector(".drop-zone-prompt").classList.add("hidden");

    const formData = new FormData();
    formData.append("image", file);

    showToast("Uploading specimen image...");

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        state.taskId = data.task_id;
        displayRawSpecimen(data.original_url);
        showToast(`Uploaded ${file.name} (${data.dimensions})`);
      } else {
        showToast(`Upload failed: ${data.error}`);
      }
    } catch (err) {
      showToast("Network error during image upload.");
    }
  }

  function displayRawSpecimen(url) {
    emptyState.classList.add("hidden");
    sideWrapper.classList.add("hidden");
    comparisonWrapper.classList.remove("hidden");

    rawImage.src = url;
    enhancedImage.src = url; // initially show raw until enhanced
    sideRawImage.src = url;
    sideEnhancedImage.src = url;

    // Reset divider to middle
    setDividerPosition(50);
  }

  // ==========================================
  // Enhancement Pipeline Trigger
  // ==========================================
  btnEnhance.addEventListener("click", async () => {
    if (!state.taskId) {
      showToast("Please load a sample or upload a specimen first!");
      return;
    }

    if (state.isProcessing) return;

    state.isProcessing = true;
    btnEnhance.querySelector(".btn-text").classList.add("hidden");
    btnEnhance.querySelector(".spinner").classList.remove("hidden");
    btnEnhance.disabled = true;

    const payload = {
      task_id: state.taskId,
      preset: state.activePreset,
      denoise_strength: parseFloat(denoiseSlider.value),
      upscale_factor: state.upscaleFactor,
      clahe_clip: parseFloat(claheSlider.value),
      sharpness: parseFloat(sharpnessSlider.value),
      flat_field: flatFieldCheckbox.checked,
    };

    try {
      const res = await fetch("/api/enhance", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (data.success) {
        state.currentMetrics = data.metrics;
        state.currentAiReport = data.ai_analysis;

        // Update image sources with cache buster
        const timestamp = new Date().getTime();
        const enhancedUrl = `${data.enhanced_url}?t=${timestamp}`;

        enhancedImage.src = enhancedUrl;
        sideEnhancedImage.src = enhancedUrl;

        // Render metrics
        renderMetrics(data.metrics);

        // Render AI report
        renderAiReport(data.ai_analysis);

        // Ensure slider view is active
        setDividerPosition(50);
        showToast("Specimen enhanced & analyzed successfully!");

        // Smooth scroll to report if desired
        reportPanel.classList.remove("hidden");
      } else {
        showToast(`Enhancement failed: ${data.error}`);
      }
    } catch (err) {
      showToast("Network error during processing.");
    } finally {
      state.isProcessing = false;
      btnEnhance.querySelector(".btn-text").classList.remove("hidden");
      btnEnhance.querySelector(".spinner").classList.add("hidden");
      btnEnhance.disabled = false;
    }
  });

  // ==========================================
  // Render Metrics & AI Report
  // ==========================================
  function renderMetrics(m) {
    valPsnr.textContent = `${m.psnr_db} dB`;
    valSnr.textContent = `${m.snr_db} dB`;
    valSsim.textContent = m.ssim.toFixed(4);

    valSharpnessMetric.textContent = `${m.enhanced_sharpness}`;
    subSharpnessGain.textContent = `+${m.sharpness_gain_percent}% membrane gain`;

    valEntropy.textContent = `${m.enhanced_entropy} bpp`;
    valResolution.textContent = m.resolution_enhanced;
  }

  function renderAiReport(ai) {
    if (!ai) return;

    aiEngineTag.textContent = ai.ai_engine || "LabClarity GenAI";
    tagModality.textContent = `Modality: ${ai.modality || "Microscopy"}`;
    tagSpecimen.textContent = `Specimen: ${ai.specimen_classification || "Cellular sample"}`;
    tagStain.textContent = `Stain: ${ai.staining_fluorophore_profile || "Assessed"}`;

    txtArtifactDiagnosis.textContent = ai.artifact_diagnosis || "N/A";
    txtMorphology.textContent = ai.morphological_features || "N/A";
    txtProtocol.textContent = ai.laboratory_methods_protocol || "N/A";

    // Recommendations list
    recList.innerHTML = "";
    const recs = ai.research_recommendations || [];
    recs.forEach((rec) => {
      const li = document.createElement("li");
      li.textContent = rec;
      recList.appendChild(li);
    });
  }

  // Copy Protocol to Clipboard
  btnCopyProtocol.addEventListener("click", () => {
    const text = txtProtocol.textContent;
    navigator.clipboard.writeText(text).then(() => {
      showToast("Methods protocol copied to clipboard!");
    });
  });

  // ==========================================
  // Export Suite
  // ==========================================
  btnExportTiff.addEventListener("click", () => {
    if (!state.taskId) return;
    window.location.href = `/api/export/tiff/${state.taskId}`;
  });

  btnExportPng.addEventListener("click", () => {
    if (!state.taskId) return;
    window.location.href = `/api/export/png/${state.taskId}`;
  });

  btnExportMd.addEventListener("click", () => {
    if (!state.taskId) return;
    window.location.href = `/api/export/report_md/${state.taskId}`;
  });

  // ==========================================
  // Split Slider Dragging Logic
  // ==========================================
  let isDragging = false;

  function setDividerPosition(percentage) {
    const clamped = Math.max(0, Math.min(100, percentage));
    sliderDivider.style.left = `${clamped}%`;
    enhancedLayer.style.width = `${clamped}%`;
  }

  sliderDivider.addEventListener("mousedown", () => {
    isDragging = true;
  });

  window.addEventListener("mouseup", () => {
    isDragging = false;
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const rect = comparisonWrapper.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const percent = (offsetX / rect.width) * 100;
    setDividerPosition(percent);
  });

  // Touch support
  sliderDivider.addEventListener("touchstart", () => {
    isDragging = true;
  });

  window.addEventListener("touchend", () => {
    isDragging = false;
  });

  window.addEventListener("touchmove", (e) => {
    if (!isDragging || !e.touches[0]) return;
    const rect = comparisonWrapper.getBoundingClientRect();
    const offsetX = e.touches[0].clientX - rect.left;
    const percent = (offsetX / rect.width) * 100;
    setDividerPosition(percent);
  });

  // ==========================================
  // View Modes (Split vs Side-by-Side)
  // ==========================================
  btnSliderMode.addEventListener("click", () => {
    btnSliderMode.classList.add("active");
    btnSideMode.classList.remove("active");
    state.viewMode = "slider";
    if (state.taskId) {
      sideWrapper.classList.add("hidden");
      comparisonWrapper.classList.remove("hidden");
    }
  });

  btnSideMode.addEventListener("click", () => {
    btnSideMode.classList.add("active");
    btnSliderMode.classList.remove("active");
    state.viewMode = "side";
    if (state.taskId) {
      comparisonWrapper.classList.add("hidden");
      sideWrapper.classList.remove("hidden");
    }
  });

  // Zoom / Inspect Toggle
  let isZoomed = false;
  btnZoomToggle.addEventListener("click", () => {
    isZoomed = !isZoomed;
    btnZoomToggle.classList.toggle("active", isZoomed);
    const scale = isZoomed ? "scale(1.8)" : "scale(1.0)";
    rawImage.style.transform = scale;
    enhancedImage.style.transform = scale;
    sideRawImage.style.transform = scale;
    sideEnhancedImage.style.transform = scale;
    showToast(isZoomed ? "Inspect Zoom: 180%" : "Inspect Zoom: Reset");
  });

  // ==========================================
  // AI Assistant Chat Modal
  // ==========================================
  btnOpenChat.addEventListener("click", () => {
    chatModal.classList.toggle("hidden");
  });

  btnCloseChat.addEventListener("click", () => {
    chatModal.classList.add("hidden");
  });

  btnSendChat.addEventListener("click", sendChatMessage);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChatMessage();
  });

  async function sendChatMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;

    // Append user message
    appendMessage(msg, "user");
    chatInput.value = "";

    // Show bot thinking
    const botLoadingId = appendMessage("Consulting biophysics model...", "bot", true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: msg,
          task_id: state.taskId,
        }),
      });
      const data = await res.json();

      const loadingElem = document.getElementById(botLoadingId);
      if (loadingElem) loadingElem.remove();

      if (data.success) {
        appendMessage(data.reply, "bot");
      } else {
        appendMessage(`Assistant error: ${data.error}`, "bot");
      }
    } catch (err) {
      const loadingElem = document.getElementById(botLoadingId);
      if (loadingElem) loadingElem.remove();
      appendMessage("Network error communicating with AI Assistant.", "bot");
    }
  }

  function appendMessage(text, sender, isLoading = false) {
    const msgDiv = document.createElement("div");
    const msgId = `msg_${Date.now()}`;
    msgDiv.id = msgId;
    msgDiv.className = `chat-msg ${sender === "user" ? "user-msg" : "bot-msg"}`;

    if (sender === "bot") {
      msgDiv.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-microscope"></i></div>
        <div class="msg-text">${text}</div>
      `;
    } else {
      msgDiv.innerHTML = `<div class="msg-text">${text}</div>`;
    }

    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgId;
  }

  // Pre-load the first sample specimen automatically on initial launch
  setTimeout(() => {
    const firstSample = document.querySelector(".sample-card");
    if (firstSample) firstSample.click();
  }, 400);
});
