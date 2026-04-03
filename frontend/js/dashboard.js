class Dashboard {
  constructor() {
    this.charts = {};
  }

  async render() {
    await Promise.all([
      this.renderStats(),
      this.renderRankings(),
      this.renderAreaChart(),
      this.renderTopPapers(),
      this.renderPapersTrend(),
      this.renderCollaborators(),
    ]);
  }

  async renderStats() {
    try {
      const stats = await API.getResearcherStats();
      document.getElementById("stat-total").textContent = stats.total_researchers || 0;
      document.getElementById("stat-avg-h").textContent = stats.avg_h_index || 0;
      document.getElementById("stat-max-h").textContent = stats.max_h_index || 0;
      document.getElementById("stat-citations").textContent = (stats.total_citations || 0).toLocaleString();
    } catch {
      console.log("Stats not available yet");
    }
  }

  async renderRankings() {
    try {
      const rankings = await API.getRankings({ limit: 20 });
      const tbody = document.getElementById("rankings-body");
      tbody.innerHTML = rankings
        .map(
          (r) => `
        <tr class="ranking-row" data-id="${r.id}">
          <td>${r.rank}</td>
          <td><strong>${r.name}</strong></td>
          <td>${r.affiliation || "—"}</td>
          <td>${r.h_index}</td>
          <td>${r.citation_count.toLocaleString()}</td>
          <td>${r.paper_count}</td>
        </tr>`
        )
        .join("");

      // Click to show ego graph
      tbody.querySelectorAll(".ranking-row").forEach((row) => {
        row.addEventListener("click", () => {
          const id = parseInt(row.dataset.id);
          if (window.graph) window.graph.renderEgo(id);
        });
      });
    } catch {
      console.log("Rankings not available yet");
    }
  }

  async renderAreaChart() {
    try {
      const areas = await API.getResearchAreas();
      if (!areas.length) return;

      const container = document.getElementById("area-chart");
      const width = container.clientWidth || 400;
      const height = 300;
      const margin = { top: 20, right: 20, bottom: 100, left: 40 };

      const svg = d3
        .select(container)
        .html("")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

      const top10 = areas.slice(0, 10);

      const x = d3
        .scaleBand()
        .domain(top10.map((d) => d.area))
        .range([margin.left, width - margin.right])
        .padding(0.2);

      const y = d3
        .scaleLinear()
        .domain([0, d3.max(top10, (d) => d.count)])
        .range([height - margin.bottom, margin.top]);

      svg
        .append("g")
        .selectAll("rect")
        .data(top10)
        .join("rect")
        .attr("x", (d) => x(d.area))
        .attr("y", (d) => y(d.count))
        .attr("width", x.bandwidth())
        .attr("height", (d) => y(0) - y(d.count))
        .attr("fill", "#4e79a7")
        .attr("rx", 3);

      svg
        .append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x))
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .attr("text-anchor", "end")
        .attr("font-size", "10px");

      svg
        .append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(y).ticks(5));
    } catch {
      console.log("Area chart not available yet");
    }
  }

  async renderTopPapers() {
    try {
      const papers = await API.getTopPapers(10);
      const list = document.getElementById("top-papers-list");
      list.innerHTML = papers
        .map(
          (p) => `
        <div class="paper-item">
          <div class="paper-title">${p.title}</div>
          <div class="paper-meta">
            ${p.venue || "—"} ${p.year || ""} &middot;
            <strong>${p.citation_count.toLocaleString()}</strong> citations
          </div>
        </div>`
        )
        .join("");
    } catch {
      console.log("Top papers not available yet");
    }
  }

  async renderPapersTrend() {
    try {
      const data = await API.getPapersByYear();
      if (!data.length) return;

      const container = document.getElementById("papers-trend");
      const width = container.clientWidth || 400;
      const height = 250;
      const margin = { top: 20, right: 20, bottom: 40, left: 50 };

      const svg = d3
        .select(container)
        .html("")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

      const recent = data.filter((d) => d.year >= 2010);

      const x = d3
        .scaleLinear()
        .domain(d3.extent(recent, (d) => d.year))
        .range([margin.left, width - margin.right]);

      const y = d3
        .scaleLinear()
        .domain([0, d3.max(recent, (d) => d.paper_count)])
        .range([height - margin.bottom, margin.top]);

      const line = d3
        .line()
        .x((d) => x(d.year))
        .y((d) => y(d.paper_count))
        .curve(d3.curveMonotoneX);

      svg
        .append("path")
        .datum(recent)
        .attr("fill", "none")
        .attr("stroke", "#e15759")
        .attr("stroke-width", 2)
        .attr("d", line);

      svg
        .append("g")
        .attr("transform", `translate(0,${height - margin.bottom})`)
        .call(d3.axisBottom(x).tickFormat(d3.format("d")));

      svg
        .append("g")
        .attr("transform", `translate(${margin.left},0)`)
        .call(d3.axisLeft(y).ticks(5));
    } catch {
      console.log("Papers trend not available yet");
    }
  }

  async renderCollaborators() {
    try {
      const data = await API.getCollaborationStats();
      const list = document.getElementById("collaborators-list");
      list.innerHTML = data
        .slice(0, 10)
        .map(
          (r, i) => `
        <div class="collab-item" data-id="${r.id}">
          <span class="collab-rank">${i + 1}.</span>
          <span class="collab-name">${r.name}</span>
          <span class="collab-count">${r.connections} connections</span>
        </div>`
        )
        .join("");

      list.querySelectorAll(".collab-item").forEach((item) => {
        item.addEventListener("click", () => {
          const id = parseInt(item.dataset.id);
          if (window.graph) window.graph.renderEgo(id);
        });
      });
    } catch {
      console.log("Collaboration stats not available yet");
    }
  }
}
