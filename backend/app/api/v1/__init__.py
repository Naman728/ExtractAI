"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1 import auth, batches, exports, guest, health, intelligence, jobs, network, results, strategy

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(guest.router)
api_router.include_router(jobs.router)
api_router.include_router(batches.router)
api_router.include_router(intelligence.router)
api_router.include_router(strategy.router)
api_router.include_router(network.router)
api_router.include_router(results.router)
api_router.include_router(exports.router)
