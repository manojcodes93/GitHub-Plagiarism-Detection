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

    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        repos,
        language,
        branch,
        threshold,
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
      document.getElementById("jobId").textContent = job.id;

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
        currentResults = job.results;
        displayResults(job.results);
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
  if (percent < 95) return "LLM reasoning and analysis...";
  if (status === "completed") return "Analysis complete!";
  return `Processing... ${percent}%`;
}

// Display results
function displayResults(results) {
  statusSection.classList.add("hidden");
  resultsSection.classList.remove("hidden");
  errorSection.classList.add("hidden");

  // Summary (adapt to new report shape)
  document.getElementById("statTotalRepos").textContent =
    1 + (results.summary.total_references || 0);
  document.getElementById("statSuspiciousPairs").textContent =
    results.summary.suspicious_references || 0;
  document.getElementById("statFilePairs").textContent =
    results.summary.total_file_pairs_compared || 0;

  // Show per-reference comparisons (candidate -> reference)
  if (results.comparisons) {
    displayComparisons(results.comparisons, results.parameters.candidate);
  } else if (results.suspicious_pairs) {
    // Backwards compatibility
    displaySuspiciousPairs(results.suspicious_pairs);
  }

  document.getElementById("downloadBtn").onclick = () =>
    downloadReport(results);
  document.getElementById("backBtn").onclick = () => resetForm();
}

// Display similarity matrix
function displayMatrix(matrix) {
  const repos = matrix.repos;
  const similarities = matrix.similarities;

  let html = '<table class="similarity-matrix"><thead><tr><th>Compare</th>';

  for (let repo of repos) {
    const name = repo.split("/").pop();
    html += `<th>${name}</th>`;
  }
  html += "</tr></thead><tbody>";

  for (let i = 0; i < repos.length; i++) {
    html += "<tr>";
    const name = repos[i].split("/").pop();
    html += `<td><strong>${name}</strong></td>`;

    for (let j = 0; j < repos.length; j++) {
      const sim = similarities[i][j];
      const cellClass = getCellClass(sim, i === j);
      const displaySim = (sim * 100).toFixed(1) + "%";

      html += `<td>
                <div class="matrix-cell ${cellClass}" onclick="showRepoComparison('${repos[i]}', '${repos[j]}')">
                    ${displaySim}
                </div>
            </td>`;
    }
    html += "</tr>";
  }

  html += "</tbody></table>";
  document.querySelector(".matrix-container").innerHTML = html;
}

// Get CSS class for matrix cell
function getCellClass(similarity, isDiagonal) {
  if (isDiagonal) return "matrix-cell-safe";
  if (similarity > 0.85) return "matrix-cell-danger";
  if (similarity > 0.75) return "matrix-cell-warning";
  return "matrix-cell-safe";
}

// Display suspicious pairs
function displaySuspiciousPairs(pairs) {
  if (pairs.length === 0) {
    document.getElementById("suspiciousList").innerHTML =
      '<p style="padding: 20px; text-align: center; color: #22c55e;">✅ No suspicious pairs detected!</p>';
    return;
  }

  let html = "";
  for (let pair of pairs) {
    const repo1 = pair.repo1.split("/").pop();
    const repo2 = pair.repo2.split("/").pop();
    const similarity = (pair.repo_similarity * 100).toFixed(1);

    html += `
        <div class="suspicious-item">
            <div class="suspicious-header">
                <span class="suspicious-title">
                    📎 ${repo1} ↔ ${repo2}
                </span>
                <span class="similarity-badge">${similarity}% Similar</span>
            </div>
            <div class="file-pairs">
                ${pair.file_pairs
                  .slice(0, 3)
                  .map(
                    (fp) => `
                    <div class="file-pair">
                        <div><span class="file-path">${fp.file1}</span> → <span class="file-path">${fp.file2}</span></div>
                        <div style="margin-top: 5px; color: #9ca3af;">
                            Similarity: ${(fp.similarity * 100).toFixed(1)}% (${fp.status})
                        </div>
                    </div>
                `,
                  )
                  .join("")}
                ${
                  pair.file_pairs.length > 3
                    ? `
                    <div class="file-pair" style="color: #6b7280; text-align: center;">
                        ... and ${pair.file_pairs.length - 3} more similar files
                    </div>
                `
                    : ""
                }
            </div>
            ${
              pair.explanation
                ? `
                <div class="explanation-text">
                    <strong>Analysis:</strong> ${pair.explanation.substring(0, 200)}...
                </div>
            `
                : ""
            }
            <button class="btn btn-secondary" onclick="showDetailsFromGlobal('${repo1}', '${repo2}', '${pair.repo1}', '${pair.repo2}')" 
                    style="margin-top: 10px; width: 100%;">
                View Details →
            </button>
        </div>
        `;
  }

  document.getElementById("suspiciousList").innerHTML = html;
}

// Display candidate -> reference comparisons
function displayComparisons(comparisons, candidate) {
  if (!comparisons || comparisons.length === 0) {
    document.getElementById("suspiciousList").innerHTML =
      '<p style="padding: 20px; text-align: center; color: #22c55e;">✅ No references compared or no similar content detected.</p>';
    return;
  }

  let html = "";
  for (let comp of comparisons) {
    const refName = comp.reference.split("/").pop();
    const similarity = (comp.repo_similarity * 100).toFixed(1);

    html += `
        <div class="suspicious-item">
            <div class="suspicious-header">
                <span class="suspicious-title">📎 ${candidate.split("/").pop()} → ${refName}</span>
                <span class="similarity-badge">${similarity}% Similar</span>
            </div>
            <div class="file-pairs">
                ${comp.file_pairs
                  .slice(0, 3)
                  .map(
                    (fp) => `
                    <div class="file-pair">
                        <div><span class="file-path">${fp.file1}</span> → <span class="file-path">${fp.file2}</span></div>
                        <div style="margin-top: 5px; color: #9ca3af;">Similarity: ${(fp.similarity * 100).toFixed(1)}% (${fp.status})</div>
                    </div>
                `,
                  )
                  .join("")}
                ${comp.file_pairs.length > 3 ? `<div class="file-pair" style="color: #6b7280; text-align: center;">... and ${comp.file_pairs.length - 3} more similar files</div>` : ""}
            </div>
            ${comp.commit_flags && comp.commit_flags.length ? `<div style="margin-top:8px;color:#f97316;">⚠️ ${comp.commit_flags.length} suspicious commits detected</div>` : ""}
            ${comp.explanation ? `<div class="explanation-text"><strong>Analysis:</strong> ${comp.explanation.substring(0, 200)}...</div>` : ""}
            <button class="btn btn-secondary" onclick="showDetailsFromGlobal('${candidate.split("/").pop()}', '${refName}', '${comp.candidate}', '${comp.reference}')" style="margin-top:10px;width:100%;">View Details →</button>
        </div>
        `;
  }

  document.getElementById("suspiciousList").innerHTML = html;
}

// Show modal with details
function showDetails(repo1, repo2, pair) {
  document.getElementById("modalTitle").textContent = `${repo1} ↔ ${repo2}`;

  let html = `
    <h4>Repository Similarity: ${(pair.repo_similarity * 100).toFixed(1)}%</h4>
    <p>Found ${pair.file_pairs.length} similar file pairs</p>

    <h5>File Pairs:</h5>
    <div class="code-block">
    `;

  for (let fp of pair.file_pairs.slice(0, 10)) {
    html += `
        <div style="margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 4px;">
            <strong>${fp.file1}</strong> → <strong>${fp.file2}</strong>
            <div style="margin-top: 5px; color: #ccc;">
                Similarity: ${(fp.similarity * 100).toFixed(1)}% | Status: ${fp.status}
            </div>
        </div>
        `;
  }

  html += "</div>";

  if (pair.explanation) {
    html += `
        <h5 style="margin-top: 20px;">Explanation:</h5>
        <div class="explanation-text">
            ${pair.explanation}
        </div>
        `;
  }

  document.getElementById("modalBody").innerHTML = html;
  modal.classList.remove("hidden");
}

// Close modal
function closeModal() {
  modal.classList.add("hidden");
}

// Download report
function downloadReport(results) {
  const json = JSON.stringify(results, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `plagiarism-report-${results.job_id}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Show status section
function showStatus() {
  document.querySelector(".analysis-form").style.display = "none";
  statusSection.classList.remove("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.add("hidden");
}

// Show error
function showError(message) {
  if (pollingInterval) clearInterval(pollingInterval);

  statusSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.remove("hidden");
  document.getElementById("errorMessage").textContent = message;
  document.getElementById("errorBackBtn").onclick = () => resetForm();
}

// Reset form
function resetForm() {
  document.querySelector(".analysis-form").style.display = "block";
  statusSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.add("hidden");
  currentJobId = null;
  currentResults = null;
  if (pollingInterval) clearInterval(pollingInterval);
}

// Show repo comparison
function showRepoComparison(repo1, repo2) {
  if (!currentResults) return;

  const pair = currentResults.suspicious_pairs.find(
    (p) =>
      (p.repo1 === repo1 && p.repo2 === repo2) ||
      (p.repo1 === repo2 && p.repo2 === repo1),
  );

  if (pair) {
    const r1 = repo1.split("/").pop();
    const r2 = repo2.split("/").pop();
    showDetails(r1, r2, pair);
  }
}

// Helper to safely show details from global results
function showDetailsFromGlobal(display1, display2, full1, full2) {
  if (!currentResults) return;

  const pair = currentResults.suspicious_pairs.find(
    (p) =>
      (p.repo1 === full1 && p.repo2 === full2) ||
      (p.repo1 === full2 && p.repo2 === full1),
  );

  if (pair) showDetails(display1, display2, pair);
}

// Close modal when clicking outside
modal.addEventListener("click", (e) => {
  if (e.target === modal || e.target.classList.contains("modal-overlay"))
    closeModal();
});

// Keyboard shortcuts
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});

console.log("CodeMirror UI loaded");

// Poll for results
function startPolling() {
  updateProgress(10, "Initializing analysis...");

  pollingInterval = setInterval(async () => {
    try {
      const response = await fetch(`/api/results/${currentJobId}`);
      if (!response.ok) throw new Error("Failed to fetch results");

      const job = await response.json();
      document.getElementById("jobId").textContent = job.id;

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
        currentResults = job.results;
        displayResults(job.results);
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
  if (percent < 95) return "LLM reasoning and analysis...";
  if (status === "completed") return "Analysis complete!";
  return `Processing... ${percent}%`;
}

// Display results
function displayResults(results) {
  // Hide status section, show results
  statusSection.classList.add("hidden");
  resultsSection.classList.remove("hidden");
  errorSection.classList.add("hidden");

  // Update summary
  document.getElementById("statTotalRepos").textContent =
    results.summary.total_repos;
  document.getElementById("statSuspiciousPairs").textContent =
    results.summary.suspicious_pairs;
  document.getElementById("statFilePairs").textContent =
    results.summary.total_file_pairs_compared;

  // Display similarity matrix
  displayMatrix(results.repository_matrix);

  // Display suspicious pairs
  displaySuspiciousPairs(results.suspicious_pairs);

  // Setup download button
  document.getElementById("downloadBtn").onclick = () =>
    downloadReport(results);
  document.getElementById("backBtn").onclick = () => resetForm();
}

// Display similarity matrix
function displayMatrix(matrix) {
  const repos = matrix.repos;
  const similarities = matrix.similarities;

  let html = '<table class="similarity-matrix"><thead><tr><th></th>';

  // Header
  for (let repo of repos) {
    const name = repo.split("/").pop();
    html += `<th>${name}</th>`;
  }
  html += "</tr></thead><tbody>";

  // Body
  for (let i = 0; i < repos.length; i++) {
    html += "<tr>";
    const name = repos[i].split("/").pop();
    html += `<td><strong>${name}</strong></td>`;

    for (let j = 0; j < repos.length; j++) {
      const sim = similarities[i][j];
      const cellClass = getCellClass(sim, i === j);
      const displaySim = (sim * 100).toFixed(1) + "%";

      html += `<td>
                <div class="matrix-cell ${cellClass}" onclick="showRepoComparison('${repos[i]}', '${repos[j]}')">
                    ${displaySim}
                </div>
            </td>`;
    }
    html += "</tr>";
  }

  html += "</tbody></table>";
  document.getElementById("similarityMatrix").innerHTML = html;
}

// Get CSS class for matrix cell
function getCellClass(similarity, isDiagonal) {
  if (isDiagonal) return "matrix-cell-safe";
  if (similarity > 0.85) return "matrix-cell-danger";
  if (similarity > 0.75) return "matrix-cell-warning";
  return "matrix-cell-safe";
}

// Display suspicious pairs
function displaySuspiciousPairs(pairs) {
  if (pairs.length === 0) {
    document.getElementById("suspiciousList").innerHTML =
      '<p style="padding: 20px; text-align: center; color: #059669;">✅ No suspicious pairs detected!</p>';
    return;
  }

  let html = "";
  for (let pair of pairs) {
    const repo1 = pair.repo1.split("/").pop();
    const repo2 = pair.repo2.split("/").pop();
    const similarity = (pair.repo_similarity * 100).toFixed(1);

    html += `
        <div class="suspicious-item">
            <div class="suspicious-header">
                <span class="suspicious-title">
                    📎 ${repo1} ↔ ${repo2}
                </span>
                <span class="similarity-badge">${similarity}% Similar</span>
            </div>
            <div class="file-pairs">
                ${pair.file_pairs
                  .slice(0, 3)
                  .map(
                    (fp) => `
                    <div class="file-pair">
                        <div><span class="file-path">${fp.file1}</span> → <span class="file-path">${fp.file2}</span></div>
                        <div style="margin-top: 5px; color: #9ca3af;">
                            Similarity: ${(fp.similarity * 100).toFixed(1)}% (${fp.status})
                        </div>
                    </div>
                `,
                  )
                  .join("")}
                ${
                  pair.file_pairs.length > 3
                    ? `
                    <div class="file-pair" style="color: #6b7280; text-align: center;">
                        ... and ${pair.file_pairs.length - 3} more similar files
                    </div>
                `
                    : ""
                }
            </div>
            ${
              pair.explanation
                ? `
                <div class="explanation-text">
                    <strong>Analysis:</strong> ${pair.explanation.substring(0, 200)}...
                </div>
            `
                : ""
            }
            <button class="btn btn-secondary" onclick="showDetailsFromGlobal('${repo1}', '${repo2}', '${pair.repo1}', '${pair.repo2}')" 
                    style="margin-top: 10px; width: 100%;">
                View Details →
            </button>
        </div>
        `;
  }

  document.getElementById("suspiciousList").innerHTML = html;
}

// Show modal with details
function showDetails(repo1, repo2, pair) {
  document.getElementById("modalTitle").textContent = `${repo1} ↔ ${repo2}`;

  let html = `
    <h4>Repository Similarity: ${(pair.repo_similarity * 100).toFixed(1)}%</h4>
    <p>Found ${pair.file_pairs.length} similar file pairs</p>

    <h5>File Pairs:</h5>
    <div class="code-block">
    `;

  for (let fp of pair.file_pairs.slice(0, 10)) {
    html += `
        <div style="margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 4px;">
            <strong>${fp.file1}</strong> → <strong>${fp.file2}</strong>
            <div style="margin-top: 5px; color: #ccc;">
                Similarity: ${(fp.similarity * 100).toFixed(1)}% | Status: ${fp.status}
            </div>
        </div>
        `;
  }

  html += "</div>";

  if (pair.explanation) {
    html += `
        <h5 style="margin-top: 20px;">Explanation:</h5>
        <div class="explanation-text">
            ${pair.explanation}
        </div>
        `;
  }

  document.getElementById("modalBody").innerHTML = html;
  modal.classList.remove("hidden");
}

// Close modal
function closeModal() {
  modal.classList.add("hidden");
}

// Download report
function downloadReport(results) {
  const json = JSON.stringify(results, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `plagiarism-report-${results.job_id}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Show status section
function showStatus() {
  form.style.display = "none";
  statusSection.classList.remove("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.add("hidden");
  document.querySelector(".analysis-form").style.marginBottom = "0";
}

// Show error
function showError(message) {
  if (pollingInterval) clearInterval(pollingInterval);

  statusSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.remove("hidden");
  document.getElementById("errorMessage").textContent = message;
  document.getElementById("errorBackBtn").onclick = () => resetForm();
}

// Reset form
function resetForm() {
  form.style.display = "block";
  statusSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  errorSection.classList.add("hidden");
  document.querySelector(".analysis-form").style.marginBottom = "40px";
  currentJobId = null;
  currentResults = null;
  if (pollingInterval) clearInterval(pollingInterval);
}

// Show repo comparison
function showRepoComparison(repo1, repo2) {
  if (!currentResults) return;

  const pair = currentResults.suspicious_pairs.find(
    (p) =>
      (p.repo1 === repo1 && p.repo2 === repo2) ||
      (p.repo1 === repo2 && p.repo2 === repo1),
  );

  if (pair) {
    const r1 = repo1.split("/").pop();
    const r2 = repo2.split("/").pop();
    showDetails(r1, r2, pair);
  }
}

// Helper to safely show details from global results
function showDetailsFromGlobal(display1, display2, full1, full2) {
  if (!currentResults) return;

  const pair = currentResults.suspicious_pairs.find(
    (p) =>
      (p.repo1 === full1 && p.repo2 === full2) ||
      (p.repo1 === full2 && p.repo2 === full1),
  );

  if (pair) showDetails(display1, display2, pair);
}

// Close modal when clicking outside
modal.addEventListener("click", (e) => {
  if (e.target === modal) closeModal();
});

// Keyboard shortcuts
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeModal();
});
