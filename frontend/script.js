const API_BASE = "http://127.0.0.1:8000";

const strengthSlider = document.getElementById("strength");
const strengthValue  = document.getElementById("strengthValue");

strengthSlider.addEventListener("input", () => {
    strengthValue.textContent = parseFloat(strengthSlider.value).toFixed(1);
});

// ================= TABS =================
function switchTab(tab, el) {
    document.querySelectorAll(".panel").forEach(p => p.style.display = "none");
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.getElementById(`tab-${tab}`).style.display = "flex";
    el.classList.add("active");
    if (tab !== "webcam" && webcamRunning) stopWebcam();
}

// ================= IMAGE =================
async function stylizeImage() {
    const fileInput = document.getElementById("imageInput");
    const style     = document.getElementById("style").value;
    const strength  = strengthSlider.value;
    const btn       = document.getElementById("imageBtn");
    const status    = document.getElementById("imageStatus");

    if (!fileInput.files.length) { alert("Please select an image."); return; }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("style", style);
    formData.append("strength", strength);

    const imageResult = document.getElementById("imageResult");
    imageResult.style.display = "none";
    btn.disabled = true;
    btn.textContent = "Processing...";
    status.textContent = "⏳ Stylizing image...";

    try {
        const response = await fetch(`${API_BASE}/stylize`, { method: "POST", body: formData });
        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const blob = await response.blob();
        imageResult.src = URL.createObjectURL(blob);
        imageResult.style.display = "block";
        imageResult.style.width = "100%";
        status.textContent = "✅ Done!";
    } catch (err) {
        alert("Error: " + err.message);
        status.textContent = "";
    } finally {
        btn.disabled = false;
        btn.textContent = "Stylize Image";
    }
}

// ================= VIDEO =================
async function stylizeVideo() {
    const fileInput = document.getElementById("videoInput");
    const style     = document.getElementById("style").value;
    const strength  = strengthSlider.value;
    const btn       = document.getElementById("videoBtn");
    const status    = document.getElementById("videoStatus");

    if (!fileInput.files.length) { alert("Please select a video."); return; }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("style", style);
    formData.append("strength", strength);

    const videoResult = document.getElementById("videoResult");
    videoResult.style.display = "none";
    btn.disabled = true;
    btn.textContent = "Processing...";
    status.textContent = "⏳ Stylizing video, this may take a while...";

    try {
        const response = await fetch(`${API_BASE}/stylize_video`, { method: "POST", body: formData });
        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const blob = await response.blob();
        const videoURL = URL.createObjectURL(blob);

        videoResult.src = videoURL;
        videoResult.load();
        videoResult.style.display = "block";
        videoResult.style.width = "100%";
        videoResult.style.visibility = "visible";
        videoResult.style.opacity = "1";
        status.textContent = "✅ Done!";
    } catch (err) {
        alert("Error: " + err.message);
        status.textContent = "";
    } finally {
        btn.disabled = false;
        btn.textContent = "Stylize Video";
    }
}

// ================= WEBCAM =================
let webcamRunning = false;
let webcamStream  = null;
let webcamLoop    = null;
let lastFrameTime = 0;
let frameCount    = 0;
let isProcessing  = false;

const FRAME_INTERVAL = 200;

async function toggleWebcam() {
    if (webcamRunning) {
        stopWebcam();
    } else {
        startWebcam();
    }
}

async function startWebcam() {
    const status = document.getElementById("webcamStatus");
    const btn    = document.getElementById("webcamBtn");

    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        const feed = document.getElementById("webcamFeed");
        feed.srcObject = webcamStream;
        await feed.play();

        webcamRunning = true;
        btn.textContent = "⏹ Stop Webcam";
        status.textContent = "🟢 Webcam running...";

        lastFrameTime = performance.now();
        frameCount = 0;

        webcamLoop = setInterval(captureAndStylize, FRAME_INTERVAL);

    } catch (err) {
        status.textContent = "❌ Could not access webcam: " + err.message;
        console.error(err);
    }
}

function stopWebcam() {
    clearInterval(webcamLoop);
    webcamLoop = null;

    if (webcamStream) {
        webcamStream.getTracks().forEach(t => t.stop());
        webcamStream = null;
    }

    const feed = document.getElementById("webcamFeed");
    feed.srcObject = null;

    webcamRunning = false;
    isProcessing = false;

    document.getElementById("webcamBtn").textContent = "▶ Start Webcam";
    document.getElementById("webcamStatus").textContent = "⚪ Webcam stopped.";
    document.getElementById("fpsDisplay").textContent = "0";
}

async function captureAndStylize() {
    if (isProcessing) return;

    const feed = document.getElementById("webcamFeed");
    if (feed.readyState < 2 || feed.videoWidth === 0) return;

    isProcessing = true;

    const style    = document.getElementById("style").value;
    const strength = strengthSlider.value;

    const canvas = document.getElementById("captureCanvas");
    canvas.width  = 320;
    canvas.height = 240;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(feed, 0, 0, 320, 240);

    canvas.toBlob(async (blob) => {
        if (!blob) { isProcessing = false; return; }

        try {
            const formData = new FormData();
            formData.append("file", blob, "frame.jpg");
            formData.append("style", style);
            formData.append("strength", strength);

            const response = await fetch(`${API_BASE}/stylize`, { method: "POST", body: formData });
            if (!response.ok) throw new Error("Failed");

            const resultBlob = await response.blob();
            const resultImg  = document.getElementById("webcamResult");
            const oldURL = resultImg.src;
            resultImg.src = URL.createObjectURL(resultBlob);
            resultImg.style.display = "block";
            if (oldURL && oldURL.startsWith("blob:")) URL.revokeObjectURL(oldURL);

            frameCount++;
            const now = performance.now();
            if (now - lastFrameTime >= 1000) {
                document.getElementById("fpsDisplay").textContent = frameCount;
                frameCount = 0;
                lastFrameTime = now;
            }

        } catch (err) {
            console.error("Frame error:", err);
        } finally {
            isProcessing = false;
        }
    }, "image/jpeg", 0.8);
}