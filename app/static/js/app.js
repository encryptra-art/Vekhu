/**
 * PULSE Client Application Logic
 * Frictionless ratings, dynamic perception cards, reporting, and instant filters.
 */

// Initialize anonymous session token
function getSessionToken() {
  let token = localStorage.getItem("pulse_session_token");
  if (!token) {
    token = "sess_" + Math.random().toString(36).substring(2) + Date.now().toString(36);
    localStorage.setItem("pulse_session_token", token);
  }
  return token;
}

// Toast notification helper
function showToast(message, type = "success") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const toast = document.createElement("div");
  toast.className = `flex items-center gap-3 px-5 py-3 rounded-full shadow-lg text-sm font-medium transition-all duration-300 transform translate-y-4 opacity-0 ${
    type === "error" 
      ? "bg-red-900 text-white" 
      : type === "warning"
      ? "bg-amber-900 text-white"
      : "bg-neutral-900 text-white"
  }`;

  const icon = type === "error" ? "⚠️" : type === "warning" ? "🔔" : "✨";
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  // Animate in
  setTimeout(() => {
    toast.classList.remove("translate-y-4", "opacity-0");
  }, 10);

  // Remove after 3.5s
  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Star rating component logic
document.addEventListener("DOMContentLoaded", () => {
  const starContainers = document.querySelectorAll(".star-rating-interactive");
  starContainers.forEach(container => {
    const stars = container.querySelectorAll("svg");
    const hiddenInput = container.parentElement.querySelector("input[name='rating']");
    let currentRating = parseInt(hiddenInput?.value || "0");

    stars.forEach(star => {
      star.addEventListener("mouseenter", () => {
        const val = parseInt(star.dataset.value);
        stars.forEach(s => {
          s.classList.toggle("hovered", parseInt(s.dataset.value) <= val);
        });
      });

      star.addEventListener("mouseleave", () => {
        stars.forEach(s => s.classList.remove("hovered"));
      });

      star.addEventListener("click", () => {
        currentRating = parseInt(star.dataset.value);
        if (hiddenInput) hiddenInput.value = currentRating;
        stars.forEach(s => {
          s.classList.toggle("active", parseInt(s.dataset.value) <= currentRating);
        });
      });
    });
  });
});

// Submit review with zero-friction anonymous parameters
async function submitReview(event) {
  event.preventDefault();
  const form = event.target;
  const submitBtn = form.querySelector("button[type='submit']");
  const originalBtnText = submitBtn.innerHTML;

  const profileId = parseInt(form.querySelector("input[name='profile_id']").value);
  const rating = parseInt(form.querySelector("input[name='rating']").value);
  const perspectiveContext = form.querySelector("select[name='perspective_context']").value;
  const headline = form.querySelector("input[name='headline']").value.trim();
  const content = form.querySelector("textarea[name='content']").value.trim();
  const authorAlias = form.querySelector("input[name='author_alias']").value.trim() || "Anonymous Observer";

  if (!rating || rating < 1 || rating > 5) {
    showToast("Please tap 1 to 5 stars to record your rating.", "warning");
    return;
  }
  if (!headline || headline.length < 3) {
    showToast("Please enter a brief headline for your perspective.", "warning");
    return;
  }
  if (!content || content.length < 10) {
    showToast("Please share at least a sentence explaining your rating (min 10 characters).", "warning");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Recording Perception...</span>`;

  try {
    const response = await fetch("/api/reviews", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-Token": getSessionToken()
      },
      body: JSON.stringify({
        profile_id: profileId,
        rating,
        perspective_context: perspectiveContext,
        headline,
        content,
        author_alias: authorAlias
      })
    });

    const result = await response.json();
    if (response.ok && result.success) {
      showToast("Your perception has been permanently recorded to the index!", "success");
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(result.detail || result.message || "Failed to submit review.", "error");
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnText;
    }
  } catch (err) {
    showToast("Network error. Please try again.", "error");
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
  }
}

// Upvote review helpfulness
async function voteHelpful(reviewId, btnElement) {
  try {
    const response = await fetch(`/api/reviews/${reviewId}/helpful`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-Token": getSessionToken()
      }
    });
    const result = await response.json();
    if (result.success) {
      const countSpan = btnElement.querySelector(".helpful-count");
      if (countSpan) countSpan.textContent = result.helpful_count;
      btnElement.classList.add("text-[#FF5E1E]", "bg-[#FF5E1E]/10");
      showToast("Marked perspective as helpful", "success");
    } else {
      showToast(result.message || "You have already upvoted this review", "warning");
    }
  } catch (err) {
    showToast("Could not record vote.", "error");
  }
}

// Generate & Download Shareable Perception Card (HTML5 Canvas)
function generatePerceptionCard(data) {
  const canvas = document.createElement("canvas");
  canvas.width = 1080;
  canvas.height = 1080;
  const ctx = canvas.getContext("2d");

  // Background - Warm bone with soft vignette
  ctx.fillStyle = "#FAF7F2";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Background subtle decorative circles mirroring reference
  const bgGrad = ctx.createRadialGradient(850, 250, 50, 850, 250, 500);
  bgGrad.addColorStop(0, "rgba(255, 94, 30, 0.18)");
  bgGrad.addColorStop(0.6, "rgba(240, 235, 226, 0.6)");
  bgGrad.addColorStop(1, "rgba(250, 247, 242, 0)");
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Floating main card container
  ctx.save();
  ctx.shadowColor = "rgba(0, 0, 0, 0.08)";
  ctx.shadowBlur = 40;
  ctx.shadowOffsetY = 20;
  ctx.fillStyle = "#FFFFFF";
  roundRect(ctx, 80, 80, 920, 920, 40);
  ctx.fill();
  ctx.restore();

  // Fine border
  ctx.strokeStyle = "rgba(18, 18, 18, 0.08)";
  ctx.lineWidth = 2;
  roundRect(ctx, 80, 80, 920, 920, 40);
  ctx.stroke();

  // Brand Header
  ctx.fillStyle = "#121212";
  ctx.font = "bold 32px 'Plus Jakarta Sans', sans-serif";
  ctx.fillText("VEKHU", 140, 160);

  // Pulse orange dot
  ctx.fillStyle = "#FF5E1E";
  ctx.beginPath();
  ctx.arc(270, 150, 8, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#76736E";
  ctx.font = "500 22px 'Plus Jakarta Sans', sans-serif";
  ctx.fillText("PUBLIC PERCEPTION INDEX", 295, 158);

  // Category Pill
  ctx.fillStyle = "#F2EFE9";
  roundRect(ctx, 140, 220, 220, 44, 22);
  ctx.fill();
  ctx.fillStyle = "#585550";
  ctx.font = "600 18px 'Plus Jakarta Sans', sans-serif";
  ctx.fillText(data.category.toUpperCase(), 165, 248);

  // Subject Name
  ctx.fillStyle = "#121212";
  ctx.font = "bold 64px 'Playfair Display', serif";
  ctx.fillText(data.name, 140, 340);

  // Subject Title
  ctx.fillStyle = "#6B6863";
  ctx.font = "400 26px 'Plus Jakarta Sans', sans-serif";
  ctx.fillText(data.title, 140, 390);

  // Big Metric Box
  ctx.fillStyle = "#FAF7F2";
  roundRect(ctx, 140, 440, 800, 220, 30);
  ctx.fill();

  // Average Rating
  ctx.fillStyle = "#121212";
  ctx.font = "bold 96px 'Plus Jakarta Sans', sans-serif";
  ctx.fillText(data.average_rating.toFixed(1), 190, 570);

  // Stars row
  ctx.fillStyle = "#FF5E1E";
  ctx.font = "40px sans-serif";
  const starCount = Math.round(data.average_rating);
  let starsStr = "★".repeat(starCount) + "☆".repeat(5 - starCount);
  ctx.fillText(starsStr, 400, 530);

  ctx.fillStyle = "#76736E";
  ctx.font = "500 24px 'Plus Jakarta Sans', sans-serif";
  ctx.fillText(`Based on ${data.rating_count} recorded community opinions`, 400, 580);

  // Featured Perspective Quote
  if (data.top_quote) {
    ctx.fillStyle = "#121212";
    ctx.font = "italic 500 26px 'Newsreader', serif";
    const quoteText = `"${data.top_quote.length > 95 ? data.top_quote.substring(0, 92) + '...' : data.top_quote}"`;
    ctx.fillText(quoteText, 140, 740);

    ctx.fillStyle = "#8C8983";
    ctx.font = "500 20px 'Plus Jakarta Sans', sans-serif";
    ctx.fillText(`— Perspective from ${data.top_quote_author || 'Anonymous Contributor'}`, 140, 785);
  }

  // Footer bar
  ctx.fillStyle = "#121212";
  roundRect(ctx, 140, 850, 800, 70, 35);
  ctx.fill();

  ctx.fillStyle = "#FFFFFF";
  ctx.font = "600 22px 'Plus Jakarta Sans', sans-serif";
  ctx.fillText("Explore the full dossier & record your opinion at vekhu.com", 200, 893);

  // Download Trigger
  const link = document.createElement("a");
  link.download = `vekhu-dossier-${data.slug}.png`;
  link.href = canvas.toDataURL("image/png");
  link.click();

  showToast("Perception Card downloaded!", "success");
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

// Modal open/close helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add("hidden");
    document.body.style.overflow = "";
  }
}

// Submit report
async function submitReport(event) {
  event.preventDefault();
  const form = event.target;
  const targetType = form.querySelector("input[name='target_type']").value;
  const targetId = parseInt(form.querySelector("input[name='target_id']").value);
  const reason = form.querySelector("select[name='reason']").value;
  const details = form.querySelector("textarea[name='details']").value.trim();

  try {
    const res = await fetch("/api/reports", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_type: targetType, target_id: targetId, reason, details })
    });
    const result = await res.json();
    if (result.success) {
      showToast("Report submitted. Our moderation team reviews all flags.", "success");
      closeModal("report-modal");
      form.reset();
    } else {
      showToast(result.message || "Failed to submit report.", "error");
    }
  } catch (err) {
    showToast("Error filing report.", "error");
  }
}

// Admin resolve report
async function resolveAdminReport(reportId, action) {
  try {
    const res = await fetch("/api/admin/reports/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ report_id: reportId, action })
    });
    const result = await res.json();
    if (result.success) {
      showToast(`Report marked as ${action}.`, "success");
      const row = document.getElementById(`report-row-${reportId}`);
      if (row) row.remove();
    } else {
      showToast(result.message || "Action failed.", "error");
    }
  } catch (err) {
    showToast("Error processing moderation action.", "error");
  }
}

// ============================================================================
// FREE FIRE PET INTERACTIVE COMPANION (Vekhu Pet System)
// Energetic Emotes, Sound Chimes (Web Audio), Particles, & Mouse Tracking
// ============================================================================

let audioCtx = null;
function getAudioContext() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) audioCtx = new AudioContext();
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

function playPetSound(type) {
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    
    if (type === 'jump') {
      [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + idx * 0.08);
        gain.gain.setValueAtTime(0.12, now + idx * 0.08);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 0.15);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + idx * 0.08);
        osc.stop(now + idx * 0.08 + 0.16);
      });
    } else if (type === 'boost') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, now);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.35);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.36);
    } else if (type === 'heart') {
      [587.33, 880.00].forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.12);
        gain.gain.setValueAtTime(0.15, now + idx * 0.12);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.12 + 0.25);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + idx * 0.12);
        osc.stop(now + idx * 0.12 + 0.26);
      });
    } else {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(600, now);
      osc.frequency.exponentialRampToValueAtTime(900, now + 0.1);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.11);
    }
  } catch(e) {}
}

const petQuotes = [
  "Let's go! Rate anyone in seconds! 🚀",
  "100% Real opinions, zero fake hype! 🔥",
  "Found a creator you love or hate? Rate them! ⭐",
  "Vekhu Level Max! Ready for honest reviews! 🐾",
  "Click me again! I love the hype! ⚡",
  "No bots allowed here—just real people! 🛡️"
];

function triggerPetEmote(type) {
  const pet = document.getElementById("vekhu-pet-char");
  const bubble = document.getElementById("vekhu-pet-speech");
  const arena = document.getElementById("freefire-arena");
  
  if (!pet) return;

  playPetSound(type);

  pet.classList.remove("pet-anim-jump", "pet-anim-boost", "pet-anim-pet", "pet-idle");
  void pet.offsetWidth; // Force reflow

  let particleIcons = [];
  if (type === "jump") {
    pet.classList.add("pet-anim-jump");
    particleIcons = ["⭐", "✨", "🎉", "🔥", "🚀"];
    if (bubble) bubble.textContent = "WOOHOO! 🚀 Let's Rate!";
  } else if (type === "boost") {
    pet.classList.add("pet-anim-boost");
    particleIcons = ["⚡", "⚡", "🔥", "💥", "✨"];
    if (bubble) bubble.textContent = "SUPERCHARGED! ⚡ 100% Honest!";
  } else if (type === "pet") {
    pet.classList.add("pet-anim-pet");
    particleIcons = ["❤️", "💖", "🐾", "🥰", "✨"];
    if (bubble) bubble.textContent = "Aww! Vekhu loves you! 🐾";
  } else {
    const randomQuote = petQuotes[Math.floor(Math.random() * petQuotes.length)];
    if (bubble) bubble.textContent = randomQuote;
    particleIcons = ["💬", "✨", "⭐"];
  }

  if (arena) {
    for (let i = 0; i < 4; i++) {
      const p = document.createElement("span");
      p.className = "emote-particle";
      p.textContent = particleIcons[Math.floor(Math.random() * particleIcons.length)];
      p.style.left = `${42 + (Math.random() * 20 - 10)}%`;
      p.style.top = `${32 + (Math.random() * 20 - 10)}%`;
      arena.appendChild(p);
      setTimeout(() => p.remove(), 1200);
    }
  }

  setTimeout(() => {
    pet.classList.remove("pet-anim-jump", "pet-anim-boost", "pet-anim-pet");
    pet.classList.add("pet-idle");
  }, 950);
}

document.addEventListener("DOMContentLoaded", () => {
  const arena = document.getElementById("freefire-arena");
  const pet = document.getElementById("vekhu-pet-char");
  
  if (arena && pet) {
    arena.addEventListener("mousemove", (e) => {
      const rect = arena.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      pet.style.transform = `perspective(600px) rotateY(${x * 18}deg) rotateX(${-y * 10}deg) scale(1.02)`;
    });

    arena.addEventListener("mouseleave", () => {
      pet.style.transform = "";
    });
  }
});

