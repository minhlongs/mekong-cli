"""FastAPI application for RaaS Marketplace."""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import PluginInfo, PluginSearchResult, Category, PluginSubmission, PluginUpdate
from .storage import MarketplaceStorage

app = FastAPI(
    title="RaaS Marketplace API",
    description="Plugin marketplace for Mekong CLI",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage backend (in-memory for now, would be PostgreSQL in production)
storage = MarketplaceStorage()


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/categories")
async def get_categories() -> List[Category]:
    """Get list of plugin categories."""
    return storage.get_categories()


@app.get("/tags")
async def get_tags() -> List[str]:
    """Get list of all tags used in marketplace."""
    return storage.get_tags()


@app.get("/plugins/featured")
async def get_featured_plugins(limit: int = Query(10, ge=1, le=50)) -> List[PluginInfo]:
    """Get featured plugins."""
    return storage.get_featured_plugins(limit)


@app.get("/plugins/trending")
async def get_trending_plugins(limit: int = Query(10, ge=1, le=50)) -> List[PluginInfo]:
    """Get trending plugins (most downloaded this week)."""
    return storage.get_trending_plugins(limit)


@app.get("/plugins")
async def search_plugins(
    q: Optional[str] = Query(None, description="Search query"),
    type: Optional[str] = Query(None, description="Filter by plugin type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("popularity", regex="^(popularity|downloads|rating|updated_at|name)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
) -> PluginSearchResult:
    """Search marketplace for plugins."""
    plugins, total = storage.search_plugins(
        query=q,
        plugin_type=type,
        tags=tags,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )

    total_pages = (total + page_size - 1) // page_size

    return PluginSearchResult(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        plugins=plugins
    )


@app.get("/plugins/{name}")
async def get_plugin_details(name: str) -> PluginInfo:
    """Get plugin details by name."""
    plugin = storage.get_plugin(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")
    return plugin


@app.get("/plugins/{name}/install")
async def get_install_info(name: str) -> Dict[str, Any]:
    """Get plugin installation information."""
    plugin = storage.get_plugin(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    if not plugin.is_installable:
        raise HTTPException(status_code=403, detail="Plugin is not available for installation")

    return {
        "name": plugin.name,
        "version": plugin.version,
        "download_url": f"https://marketplace.mekong.dev/downloads/{name}-{plugin.version}.py",
        "checksum": plugin.checksum,
        "manifest_url": f"https://marketplace.mekong.dev/manifests/{name}.json",
        "mcu_cost": plugin.mcu_cost
    }


@app.post("/plugins/{name}/rate")
async def rate_plugin(
    name: str,
    rating: int = Field(..., ge=1, le=5),
    comment: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """Submit a rating for a plugin."""
    if not (1 <= rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    plugin = storage.get_plugin(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    storage.add_rating(name, rating, comment, user_id)

    return {
        "status": "success",
        "message": f"Rating submitted for {name}",
        "plugin": name,
        "rating": rating
    }


@app.post("/plugins/submit")
async def submit_plugin(
    submission: PluginSubmission
) -> Dict[str, Any]:
    """Submit a new plugin for marketplace listing."""
    # Validate submission
    plugin_id = storage.submit_plugin(submission)

    return {
        "status": "received",
        "plugin_id": plugin_id,
        "message": "Plugin submitted for review",
        "review_url": f"/admin/submissions/{plugin_id}"
    }


@app.get("/plugins/{name}/downloads/stats")
async def get_download_stats(name: str) -> Dict[str, Any]:
    """Get download statistics for a plugin (developer endpoint)."""
    plugin = storage.get_plugin(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    stats = storage.get_download_stats(name)
    return {
        "plugin": name,
        "total_downloads": plugin.downloads,
        "period": stats.get("period", "all_time"),
        "breakdown": stats.get("breakdown", {})
    }


@app.get("/developer/plugins")
async def list_developer_plugins(
    developer: str = Query(..., description="Developer identifier")
) -> List[PluginInfo]:
    """List all plugins by a developer."""
    return storage.get_plugins_by_developer(developer)


@app.post("/developer/plugins/{name}/update")
async def update_plugin(
    name: str,
    update: PluginUpdate
) -> Dict[str, Any]:
    """Update plugin metadata (developer endpoint)."""
    plugin = storage.get_plugin(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    storage.update_plugin(name, update.dict(exclude_unset=True))

    return {
        "status": "success",
        "message": f"Plugin {name} updated"
    }
