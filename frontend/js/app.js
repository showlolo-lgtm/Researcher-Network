let graph;
let dashboard;

// Show researcher detail in sidebar
window.showResearcherDetail = function (d) {
  const panel = document.getElementById("detail-panel");
  panel.innerHTML = `
    <h3>${d.name}</h3>
    <p class="detail-affiliation">${d.affiliation || "Unknown affiliation"}</p>
    <div class="detail-stats">
      <div class="detail-stat"><span class="stat-value">${d.h_index}</span><span class="stat-label">h-index</span></div>
      <div class="detail-stat"><span class="stat-value">${d.citation_count.toLocaleString()}</span><span class="stat-label">Citations</span></div>
    </div>
    <div class="detail-areas">
      <strong>Research Areas:</strong>
      <div class="area-tags">${(d.research_areas || []).map((a) => `<span class="area-tag">${a}</span>`).join("")}</div>
    </div>
    <button class="btn-ego" onclick="graph.renderEgo(${d.id})">Show Network</button>
  `;
  panel.style.display = "block";
};

// Filter controls
function setupFilters() {
  const form = document.getElementById("filter-form");
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const params = {};
    const minH = document.getElementById("filter-h-index").value;
    const area = document.getElementById("filter-area").value;
    const tier = document.getElementById("filter-tier").value;
    const limit = document.getElementById("filter-limit").value;

    if (minH) params.min_h_index = parseInt(minH);
    if (area) params.research_area = area;
    if (tier) params.max_tier = parseInt(tier);
    if (limit) params.limit = parseInt(limit);

    graph.render(params);
  });

  document.getElementById("btn-reset").addEventListener("click", () => {
    document.getElementById("filter-form").reset();
    graph.render();
  });
}

// Tab switching
function setupTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");

      if (btn.dataset.tab === "tab-graph") {
        graph.render();
      }
    });
  });
}

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
  graph = new NetworkGraph("graph-container");
  window.graph = graph;
  dashboard = new Dashboard();

  setupFilters();
  setupTabs();

  // Load initial data
  graph.render();
  dashboard.render();
});
