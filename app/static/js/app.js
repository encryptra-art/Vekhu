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
