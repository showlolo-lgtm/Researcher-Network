from fastapi import APIRouter

from app.api import analytics, graph, institutions, papers, relationships, researchers

api_router = APIRouter(prefix="/api")

api_router.include_router(researchers.router)
api_router.include_router(papers.router)
api_router.include_router(institutions.router)
api_router.include_router(relationships.router)
api_router.include_router(graph.router)
api_router.include_router(analytics.router)
