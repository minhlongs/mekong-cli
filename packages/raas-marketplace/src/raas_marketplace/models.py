"""Data models for RaaS Marketplace."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class PluginInfo(BaseModel):
    """Plugin information returned by marketplace API."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: str = "agent"
    downloads: int = 0
    rating: float = Field(0.0, ge=0.0, le=5.0)
    rating_count: int = 0
    tags: List[str] = Field(default_factory=list)
    repository_url: str = ""
    documentation_url: str = ""
    created_at: str = ""
    updated_at: str = ""
    license: str = "MIT"
    min_mekong_version: str = ""
    dependencies: List[str] = Field(default_factory=list)
    is_paid: bool = False
    price: Optional[float] = None
    is_featured: bool = False
    checksum: str = ""
    mcu_cost: int = 1

    @validator('rating')
    def rating_range(cls, v):
        """Ensure rating is between 0 and 5."""
        if not (0 <= v <= 5):
            raise ValueError('Rating must be between 0 and 5')
        return v


class PluginSearchResult(BaseModel):
    """Search result pagination."""
    total: int
    page: int
    page_size: int
    total_pages: int
    plugins: List[PluginInfo]


class Category(BaseModel):
    """Plugin category."""
    name: str
    slug: str
    description: str = ""
    plugin_count: int = 0


class PluginSubmission(BaseModel):
    """Plugin submission for marketplace."""
    name: str
    version: str
    description: str
    author: str
    author_email: str
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    license: str = "MIT"
    tags: List[str] = Field(default_factory=list)
    plugin_type: str = "agent"
    dependencies: List[str] = Field(default_factory=list)
    min_mekong_version: str = "6.0.0"
    manifest_url: str  # URL to plugin.v2.json
    download_url: str  # URL to plugin .py file or package
    checksum: str
    is_paid: bool = False
    price: Optional[float] = None


class PluginUpdate(BaseModel):
    """Plugin metadata update."""
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    is_paid: Optional[bool] = None
    price: Optional[float] = None


class Rating(BaseModel):
    """User rating/review."""
    plugin_name: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DownloadStats(BaseModel):
    """Download statistics."""
    plugin_name: str
    total: int
    period: str = "all_time"
    breakdown: Dict[str, int] = Field(default_factory=dict)
