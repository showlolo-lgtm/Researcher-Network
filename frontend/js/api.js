const API = {
  async get(url, params = {}) {
    const query = new URLSearchParams(params).toString();
    const fullUrl = query ? `${url}?${query}` : url;
    const resp = await fetch(fullUrl);
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
  },

  getGraph(params = {}) {
    return this.get("/api/graph", params);
  },

  getEgoGraph(researcherId, maxTier = 2) {
    return this.get(`/api/graph/ego/${researcherId}`, { max_tier: maxTier });
  },

  getResearchers(params = {}) {
    return this.get("/api/researchers", params);
  },

  getResearcher(id) {
    return this.get(`/api/researchers/${id}`);
  },

  getResearcherStats() {
    return this.get("/api/researchers/stats/summary");
  },

  getRankings(params = {}) {
    return this.get("/api/analytics/rankings", params);
  },

  getResearchAreas() {
    return this.get("/api/analytics/research-areas");
  },

  getTopPapers(limit = 20) {
    return this.get("/api/analytics/top-papers", { limit });
  },

  getPapersByYear() {
    return this.get("/api/analytics/papers-by-year");
  },

  getCollaborationStats() {
    return this.get("/api/analytics/collaboration-stats");
  },

  getInstitutions(type = null) {
    const params = type ? { type } : {};
    return this.get("/api/institutions", params);
  },

  getInstitutionDistribution() {
    return this.get("/api/institutions/stats/distribution");
  },
};
