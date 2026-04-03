class NetworkGraph {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight || 600;
    this.simulation = null;
    this.svg = null;
    this.tooltip = null;
    this.init();
  }

  init() {
    this.svg = d3
      .select(this.container)
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("viewBox", [0, 0, this.width, this.height]);

    // Zoom behavior
    const zoom = d3.zoom().scaleExtent([0.1, 8]).on("zoom", (event) => {
      this.g.attr("transform", event.transform);
    });
    this.svg.call(zoom);

    this.g = this.svg.append("g");

    // Tooltip
    this.tooltip = d3
      .select(this.container)
      .append("div")
      .attr("class", "tooltip")
      .style("opacity", 0);

    // Legend
    this.addLegend();
  }

  addLegend() {
    const legend = this.svg.append("g").attr("transform", "translate(20, 20)");
    const types = [
      { label: "University", color: "#4e79a7" },
      { label: "Research Institute", color: "#e15759" },
      { label: "Company", color: "#59a14f" },
      { label: "Unknown", color: "#999" },
    ];

    types.forEach((t, i) => {
      const row = legend.append("g").attr("transform", `translate(0, ${i * 22})`);
      row.append("circle").attr("r", 6).attr("cx", 6).attr("cy", 0).attr("fill", t.color);
      row
        .append("text")
        .attr("x", 18)
        .attr("y", 4)
        .attr("font-size", "12px")
        .attr("fill", "#333")
        .text(t.label);
    });
  }

  getColor(institutionType) {
    const colors = {
      university: "#4e79a7",
      research_institute: "#e15759",
      company: "#59a14f",
    };
    return colors[institutionType] || "#999";
  }

  getTierStyle(tier) {
    const styles = {
      1: { width: 3, opacity: 0.8, dash: "" },
      2: { width: 1.5, opacity: 0.5, dash: "" },
      3: { width: 0.8, opacity: 0.3, dash: "4,4" },
    };
    return styles[tier] || styles[3];
  }

  async render(params = {}) {
    const data = await API.getGraph(params);
    this.draw(data);
  }

  async renderEgo(researcherId) {
    const data = await API.getEgoGraph(researcherId);
    this.draw(data, researcherId);
  }

  draw(data, centerId = null) {
    this.g.selectAll("*").remove();

    if (!data.nodes.length) {
      this.g
        .append("text")
        .attr("x", this.width / 2)
        .attr("y", this.height / 2)
        .attr("text-anchor", "middle")
        .attr("fill", "#999")
        .attr("font-size", "16px")
        .text("No data available. Run seed ingestion first (POST /api/ingest/seed).");
      return;
    }

    const nodeMap = new Map(data.nodes.map((n) => [n.id, n]));

    // Filter links to only include nodes we have
    const links = data.links.filter((l) => nodeMap.has(l.source) && nodeMap.has(l.target));

    // Scale node radius by h-index
    const hIndices = data.nodes.map((n) => n.h_index).filter((h) => h > 0);
    const radiusScale = d3
      .scaleSqrt()
      .domain([0, d3.max(hIndices) || 1])
      .range([4, 25]);

    // Force simulation
    this.simulation = d3
      .forceSimulation(data.nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance((d) => 80 + (d.tier - 1) * 40)
      )
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(this.width / 2, this.height / 2))
      .force("collision", d3.forceCollide().radius((d) => radiusScale(d.h_index) + 2));

    // Draw links
    const link = this.g
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", "#aaa")
      .attr("stroke-width", (d) => this.getTierStyle(d.tier).width)
      .attr("stroke-opacity", (d) => this.getTierStyle(d.tier).opacity)
      .attr("stroke-dasharray", (d) => this.getTierStyle(d.tier).dash);

    // Draw nodes
    const node = this.g
      .append("g")
      .selectAll("g")
      .data(data.nodes)
      .join("g")
      .attr("cursor", "pointer")
      .call(this.drag(this.simulation));

    node
      .append("circle")
      .attr("r", (d) => radiusScale(d.h_index))
      .attr("fill", (d) => this.getColor(d.institution_type))
      .attr("stroke", (d) => (d.id === centerId ? "#ff6b35" : "#fff"))
      .attr("stroke-width", (d) => (d.id === centerId ? 3 : 1.5))
      .attr("opacity", 0.85);

    // Labels for larger nodes
    node
      .filter((d) => d.h_index > (d3.median(hIndices) || 0))
      .append("text")
      .attr("dy", (d) => radiusScale(d.h_index) + 14)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("fill", "#333")
      .text((d) => d.name.length > 15 ? d.name.slice(0, 15) + "..." : d.name);

    // Hover interactions
    node
      .on("mouseover", (event, d) => {
        this.tooltip
          .style("opacity", 1)
          .html(
            `<strong>${d.name}</strong><br/>` +
              `${d.affiliation || "Unknown"}<br/>` +
              `h-index: ${d.h_index} | Citations: ${d.citation_count.toLocaleString()}<br/>` +
              `Areas: ${(d.research_areas || []).slice(0, 3).join(", ") || "N/A"}`
          )
          .style("left", event.offsetX + 15 + "px")
          .style("top", event.offsetY - 10 + "px");
      })
      .on("mouseout", () => {
        this.tooltip.style("opacity", 0);
      })
      .on("click", (event, d) => {
        this.renderEgo(d.id);
        // Update detail panel
        if (window.showResearcherDetail) {
          window.showResearcherDetail(d);
        }
      });

    // Tick
    this.simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });
  }

  drag(simulation) {
    return d3
      .drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }
}
