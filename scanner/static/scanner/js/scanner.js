/**
 * QR Code Scanner Client Script for TechPass Event Check-In
 * Powered by Html5Qrcode Library & Django CSRF API
 */

document.addEventListener('DOMContentLoaded', () => {
  let html5Qrcode = null;
  let currentCameraId = null;
  let isProcessing = false;
  let soundEnabled = true;

  const readerElement = document.getElementById('reader');
  const resultCard = document.getElementById('resultCard');
  const cameraSelect = document.getElementById('cameraSelect');
  const startBtn = document.getElementById('startScanBtn');
  const stopBtn = document.getElementById('stopScanBtn');
  const soundToggleBtn = document.getElementById('soundToggleBtn');
  const manualTokenForm = document.getElementById('manualTokenForm');

  // Web Audio API Sound Feedback
  function playAudioTone(type) {
    if (!soundEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.connect(gain);
      gain.connect(audioCtx.destination);

      if (type === 'success') {
        // High double chime
        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
        osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.1); // A5
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.3);
      } else if (type === 'warning') {
        // Warning buzz
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(300, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
      } else {
        // Low error tone
        osc.type = 'square';
        osc.frequency.setValueAtTime(180, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.4, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
        osc.start();
        osc.stop(audioCtx.currentTime + 0.4);
      }
    } catch (e) {
      console.warn("Audio playback unsupported or blocked:", e);
    }
  }

  // Get Django CSRF Token from cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Initialize and List Cameras
  async function setupCameras() {
    try {
      const devices = await Html5Qrcode.getCameras();
      if (devices && devices.length) {
        cameraSelect.innerHTML = '';
        devices.forEach((device, index) => {
          const option = document.createElement('option');
          option.value = device.id;
          option.text = device.label || `Camera ${index + 1}`;
          // Prefer back environment camera
          if (device.label.toLowerCase().includes('back') || device.label.toLowerCase().includes('environment')) {
            option.selected = true;
          }
          cameraSelect.appendChild(option);
        });

        currentCameraId = cameraSelect.value;
        startScanner(currentCameraId);
      } else {
        showErrorUI("No camera devices found on this device.");
      }
    } catch (err) {
      console.error("Camera detection error:", err);
      showErrorUI("Camera permission denied or camera unavailable. Please grant camera access in browser settings.");
    }
  }

  // Start Camera Scanning
  function startScanner(cameraId) {
    if (!html5Qrcode) {
      html5Qrcode = new Html5Qrcode("reader");
    }

    const config = {
      fps: 10,
      qrbox: { width: 220, height: 220 },
      aspectRatio: 1.0
    };

    const cameraMode = cameraId ? { deviceId: { exact: cameraId } } : { facingMode: "environment" };

    html5Qrcode.start(
      cameraMode,
      config,
      onScanSuccess,
      onScanError
    ).then(() => {
      startBtn.classList.add('d-none');
      stopBtn.classList.remove('d-none');
      document.getElementById('scannerPlaceholder')?.classList.add('d-none');
      document.getElementById('scannerOverlay')?.classList.remove('d-none');
    }).catch((err) => {
      console.error("Scanner start error:", err);
      showErrorUI("Failed to start camera feed. Please select a different camera or check permissions.");
    });
  }

  // Stop Camera Scanning
  function stopScanner() {
    if (html5Qrcode) {
      html5Qrcode.stop().then(() => {
        html5Qrcode.clear();
        startBtn.classList.remove('d-none');
        stopBtn.classList.add('d-none');
        document.getElementById('scannerOverlay')?.classList.add('d-none');
      }).catch(err => console.error("Scanner stop error:", err));
    }
  }

  // Process Scanned QR Code
  async function onScanSuccess(decodedText, decodedResult) {
    if (isProcessing) return;
    isProcessing = true;

    // Pause camera scan while verifying
    if (html5Qrcode) {
      try { html5Qrcode.pause(); } catch(e) {}
    }

    await processToken(decodedText);
  }

  function onScanError(errorMessage) {
    // Ignore routine frame scan misses
  }

  // Send Token to Django API
  async function processToken(tokenStr) {
    showLoadingUI();
    const csrfToken = getCookie('csrftoken');

    try {
      const response = await fetch('/scanner/api/check-in/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ token: tokenStr })
      });

      const data = await response.json();
      displayScanResult(data);
    } catch (error) {
      console.error("Check-in API error:", error);
      displayScanResult({
        success: false,
        message: 'Network / server communication error. Please try again.'
      });
    }
  }

  // Render Result Feedback Card
  function displayScanResult(data) {
    resultCard.classList.remove('d-none', 'success', 'warning', 'danger');

    if (data.success) {
      playAudioTone('success');
      resultCard.classList.add('success');
      resultCard.innerHTML = `
        <div class="d-flex align-items-center gap-3">
          <div class="bg-success text-white rounded-circle d-flex align-items-center justify-content-center p-3 fs-3" style="width:56px; height:56px;">
            <i class="bi bi-check-lg"></i>
          </div>
          <div class="flex-grow-1">
            <h5 class="fw-bold text-success mb-0"><i class="bi bi-check-circle-fill me-1"></i> Check-in Successful</h5>
            <div class="mt-2 fs-5 fw-bold text-dark">${escapeHtml(data.participant.name)}</div>
            <div class="text-muted small">Roll No: <strong>${escapeHtml(data.participant.roll_number)}</strong> &bull; ${escapeHtml(data.participant.email)}</div>
            <div class="mt-1 extra-small text-secondary"><i class="bi bi-clock me-1"></i>Checked in at ${escapeHtml(data.checked_in_at)}</div>
          </div>
        </div>
        <div class="mt-3 text-end">
          <button id="resumeScanBtn" class="btn btn-success btn-sm px-4 rounded-pill fw-bold">
            <i class="bi bi-arrow-repeat me-1"></i> Scan Next Participant
          </button>
        </div>
      `;
    } else if (data.message && data.message.includes('already checked in')) {
      playAudioTone('warning');
      resultCard.classList.add('warning');
      resultCard.innerHTML = `
        <div class="d-flex align-items-center gap-3">
          <div class="bg-warning text-dark rounded-circle d-flex align-items-center justify-content-center p-3 fs-3" style="width:56px; height:56px;">
            <i class="bi bi-exclamation-lg"></i>
          </div>
          <div class="flex-grow-1">
            <h5 class="fw-bold text-warning-emphasis mb-0"><i class="bi bi-exclamation-triangle-fill me-1"></i> Already Checked In</h5>
            ${data.participant ? `
              <div class="mt-2 fs-5 fw-bold text-dark">${escapeHtml(data.participant.name)}</div>
              <div class="text-muted small">Roll No: <strong>${escapeHtml(data.participant.roll_number)}</strong></div>
              <div class="mt-1 extra-small text-secondary"><i class="bi bi-clock me-1"></i>Previously checked in: ${escapeHtml(data.checked_in_at)}</div>
            ` : `<div class="text-muted mt-1">${escapeHtml(data.message)}</div>`}
          </div>
        </div>
        <div class="mt-3 text-end">
          <button id="resumeScanBtn" class="btn btn-warning btn-sm px-4 rounded-pill fw-bold text-dark">
            <i class="bi bi-arrow-repeat me-1"></i> Continue Scanning
          </button>
        </div>
      `;
    } else {
      playAudioTone('error');
      resultCard.classList.add('danger');
      resultCard.innerHTML = `
        <div class="d-flex align-items-center gap-3">
          <div class="bg-danger text-white rounded-circle d-flex align-items-center justify-content-center p-3 fs-3" style="width:56px; height:56px;">
            <i class="bi bi-x-lg"></i>
          </div>
          <div class="flex-grow-1">
            <h5 class="fw-bold text-danger mb-0"><i class="bi bi-x-circle-fill me-1"></i> Invalid QR Code</h5>
            <div class="text-secondary small mt-1">${escapeHtml(data.message)}</div>
          </div>
        </div>
        <div class="mt-3 text-end">
          <button id="resumeScanBtn" class="btn btn-danger btn-sm px-4 rounded-pill fw-bold">
            <i class="bi bi-arrow-repeat me-1"></i> Try Again
          </button>
        </div>
      `;
    }

    // Attach resume scanner click handler
    document.getElementById('resumeScanBtn')?.addEventListener('click', () => {
      resumeScanning();
    });
  }

  function resumeScanning() {
    resultCard.classList.add('d-none');
    isProcessing = false;
    if (html5Qrcode) {
      try { html5Qrcode.resume(); } catch(e) {}
    }
  }

  function showLoadingUI() {
    resultCard.classList.remove('d-none');
    resultCard.className = 'scan-result-card bg-white border p-3 shadow-sm';
    resultCard.innerHTML = `
      <div class="d-flex align-items-center gap-3">
        <div class="spinner-border text-primary" role="status"></div>
        <div>
          <div class="fw-bold">Verifying Participant...</div>
          <div class="text-muted small">Checking token with Django backend</div>
        </div>
      </div>
    `;
  }

  function showErrorUI(msg) {
    const placeholder = document.getElementById('scannerPlaceholder');
    if (placeholder) {
      placeholder.innerHTML = `
        <div class="text-danger p-4 text-center">
          <i class="bi bi-camera-video-off fs-1 mb-2 d-block"></i>
          <p class="mb-0 fw-semibold">${escapeHtml(msg)}</p>
        </div>
      `;
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, function(m) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
    });
  }

  // Event Listeners
  startBtn?.addEventListener('click', () => startScanner(cameraSelect.value));
  stopBtn?.addEventListener('click', stopScanner);

  cameraSelect?.addEventListener('change', (e) => {
    stopScanner();
    setTimeout(() => startScanner(e.target.value), 300);
  });

  soundToggleBtn?.addEventListener('click', () => {
    soundEnabled = !soundEnabled;
    soundToggleBtn.classList.toggle('btn-success', soundEnabled);
    soundToggleBtn.classList.toggle('btn-secondary', !soundEnabled);
    soundToggleBtn.innerHTML = soundEnabled ? '<i class="bi bi-volume-up-fill"></i> Sound ON' : '<i class="bi bi-volume-mute-fill"></i> Sound OFF';
  });

  manualTokenForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const tokenInput = document.getElementById('manualTokenInput');
    const val = tokenInput.value.strip ? tokenInput.value.strip() : tokenInput.value.trim();
    if (val) {
      processToken(val);
      tokenInput.value = '';
      const modalEl = document.getElementById('manualTokenModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
    }
  });

  // Start Camera System on load
  setupCameras();
});
