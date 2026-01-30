// CodeMirror - Frontend JavaScript

// State management
let currentJobId = null;
let currentResults = null;
let pollingInterval = null;

// DOM Elements
const form = document.getElementById("analyzeForm");
const statusSection = document.getElementById("statusSection");
const resultsSection = document.getElementById("resultsSection");
const errorSection = document.getElementById("errorSection");
const modal = document.getElementById("detailsModal");

// Form submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const repos = Array.from(document.querySelectorAll(".repo-url"))
    .map((input) => input.value.trim())
    .filter((url) => url && url.startsWith("http"));

  if (repos.length < 3) {
    showError(
      "Provide candidate (first) and at least 2 reference repositories",
    );
    return;
  }

  const language = document.getElementById("language").value;
  const branch = document.getElementById("branch").value;
  const threshold = parseFloat(
    document.getElementById("thresholdSlider").value,
  );

  await submitAnalysis(repos, language, branch, threshold);
});

// Submit analysis
async function submitAnalysis(repos, language, branch, threshold) {
  try {
    showStatus();
    updateProgress(0, "Submitting analysis...");

    // First repo is candidate, rest are references
    const candidate = { url: repos[0], branch: branch };
    const references = repos
      .slice(1)
      .map((url) => ({ url: url, branch: branch }));

    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate: candidate,
        references: references,
        language: language,
        branch: branch,
        threshold: threshold,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Analysis submission failed");
    }

    const data = await response.json();
    currentJobId = data.job_id;

    // Start polling for results
    startPolling();
  } catch (error) {
    showError(error.message);
  }
}

// Poll for results
function startPolling() {
  updateProgress(10, "Initializing analysis...");

  pollingInterval = setInterval(async () => {
    try {
      const response = await fetch(`/api/results/${currentJobId}`);
      if (!response.ok) throw new Error("Failed to fetch results");

      const job = await response.json();
      document.getElementById("jobId").textContent = job.job_id;

      // Update status badge
      const statusBadge = document.getElementById("status");
      statusBadge.className = `status-badge status-${job.status}`;
      statusBadge.textContent =
        job.status.charAt(0).toUpperCase() + job.status.slice(1);

      // Update progress
      updateProgress(job.progress, getProgressText(job.progress, job.status));

      // Handle completion
      if (job.status === "completed") {
        clearInterval(pollingInterval);
        currentResults = job.data;
        displayResults(job.data);
      } else if (job.status === "failed") {
        clearInterval(pollingInterval);
        showError(job.error || "Analysis failed");
      }
    } catch (error) {
      console.error("Polling error:", error);
    }
  }, 2000);
}

// Update progress display
function updateProgress(percent, text) {
  document.getElementById("progressFill").style.width = percent + "%";
  document.getElementById("progressPercent").textContent = percent + "%";
}

// Get progress text based on percentage
function getProgressText(percent, status) {
  if (percent < 25) return "Cloning repositories...";
  if (percent < 40) return "Extracting source files...";
  if (percent < 60) return "Preprocessing code...";
  if (percent < 75) return "Generating embeddings...";
  if (percent < 85) return "Computing similarity...";
  if (percent < 95) return "Analyzing plagiarism...";
  if (status === "completed") return "Analysis complete!";
  return `Processing... ${percent}%`;
}

// Display results
function displayResults(results) {
  statusSection.classList.add("hidden");
  resultsSection.classList.remove("hidden");
  errorSection.classList.add("hidden");

  if (!results) {
    showError("No results available");
    return;
  }

  // Summary
  const candidate_files = results.candidate?.files_count || 0;
  const total_references = results.analysis_config?.total_references || 0;

  document.getElementById("statTotalRepos").textContent = 1 + total_references;
  document.getElementById("statSuspiciousPairs").textContent = Object.values(
    results.plagiarism_reports || {},
  ).filter((r) => r.repository_judgment === "PLAGIARISM").length;
  document.getElementById("statFilePairs").textContent = Object.values(
    results.comparisons || {},
  ).reduce((sum, c) => sum + Object.keys(c.files || {}).length, 0);

  // Display per-reference comparisons
  displayComparisons(results);

  document.getElementById("downloadBtn").onclick = () =>
    downloadReport(results);
  document.getElementById("backBtn").onclick = () => resetForm();
}

// Display candidate -> reference comparisons
function displayComparisons(results) {
  const comparisons = results.plagiarism_reports || {};
  const candidate_url = results.candidate?.url || "Unknown";

  if (Object.keys(comparisons).length === 0) {
    document.getElementById("suspiciousList").innerHTML =
      '<p style="padding: 20px; text-align: center; color: #22c55e;">✅ No suspicious similarities detected!</p>';
    return;
  }

  let html = "";
  for (const [ref_url, report] of Object.entries(comparisons)) {
    const refName = ref_url.split("/").pop();
    const candName = candidate_url.split("/").pop();
    const similarity = (report.similarity_score * 100).toFixed(1);
    const verdict = report.repository_judgment;
    const verdictClass =
      verdict === "PLAGIARISM"
        ? "verdict-plagiarism"
        : verdict === "SUSPICIOUS"
          ? "verdict-suspicious"
          : "verdict-clean";

    html += `
      <div class="suspicious-item">
        <div class="suspicious-header">
          <span class="suspicious-title">📎 ${candName} → ${refName}</span>
          <span class="similarity-badge">${similarity}% Similar</span>
        </div>
        <div style="margin: 10px 0;">
          <span class="verdict-badge ${verdictClass}">${verdict}</span>
        </div>
        <p style="margin: 10px 0; font-size: 14px; color: #6b7280;">${report.explanation}</p>
        <button class="btn btn-secondary" onclick="showModal('${refName}', '${escape(JSON.stringify(report))}')" style="margin-top: 10px; width: 100%;">
          View Details →
        </button>
      </div>
    `;
  }

  document.getElementById("suspiciousList").innerHTML = html;
}

// Show status section
function showStatus() {
  const mainContainer = document.getElementById("mainContainer");
  mainContainer.style.display = "block";
  statusSection.classList.remove("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.add("hidden");
}

// Show error
function showError(message) {
  if (pollingInterval) clearInterval(pollingInterval);

  const mainContainer = document.getElementById("mainContainer");
  mainContainer.style.display = "block";
  statusSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.remove("hidden");
  document.getElementById("errorMessage").textContent = message;
  document.getElementById("errorBackBtn").onclick = () => resetForm();
}

// Reset form
function resetForm() {
  document.getElementById("analyzeForm").reset();
  const mainContainer = document.getElementById("mainContainer");
  const heroSection = document.getElementById("heroSection");
  mainContainer.style.display = "none";
  heroSection.style.display = "block";
  currentJobId = null;
  currentResults = null;
  if (pollingInterval) clearInterval(pollingInterval);
}

// Download report
function downloadReport(results) {
  const json = JSON.stringify(results, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `plagiarism_report_${currentJobId}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

// Show modal with details
function showModal(title, data) {
  document.getElementById("modalTitle").textContent = title;
  const parsed = JSON.parse(unescape(data));
  let content = `<pre>${JSON.stringify(parsed, null, 2)}</pre>`;
  document.getElementById("modalBody").innerHTML = content;
  modal.classList.remove("hidden");
}

// Close modal
function closeModal() {
  modal.classList.add("hidden");
}

// Navigation functions
function scrollToAnalysis() {
  const mainContainer = document.getElementById("mainContainer");
  const heroSection = document.getElementById("heroSection");
  heroSection.style.display = "none";
  mainContainer.style.display = "block";
  document
    .getElementById("analysisSection")
    .scrollIntoView({ behavior: "smooth" });
}

function scrollToDashboard() {
  scrollToAnalysis();
  document
    .getElementById("analysisSection")
    .scrollIntoView({ behavior: "smooth" });
}

function goHome(e) {
  if (e) e.preventDefault();
  resetForm();
}
