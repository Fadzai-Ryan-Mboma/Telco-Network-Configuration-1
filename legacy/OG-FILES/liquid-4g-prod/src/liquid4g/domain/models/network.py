"""
Network Domain Models

Represents physical network infrastructure:
- Network sites (eNodeB locations)
- Network cells (individual cells within sites)
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SiteStatus(str, Enum):
    """Site operational status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class NetworkSite(BaseModel):
    """
    Network Site (eNodeB location)

    Represents a physical site with one or more cells.
    """

    id: Optional[int] = Field(default=None, description="Database ID")
    site_id: str = Field(..., description="Unique site identifier", min_length=1)
    site_name: str = Field(..., description="Human-readable site name", min_length=1)
    location: Optional[str] = Field(default=None, description="Physical address")
    latitude: Optional[float] = Field(default=None, ge=-90, le=90, description="GPS latitude")
    longitude: Optional[float] = Field(default=None, ge=-180, le=180, description="GPS longitude")
    region: Optional[str] = Field(default=None, description="Geographic region")
    status: SiteStatus = Field(default=SiteStatus.ACTIVE, description="Operational status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("site_id")
    @classmethod
    def validate_site_id(cls, v: str) -> str:
        """Validate site ID format"""
        if not v or v.isspace():
            raise ValueError("Site ID cannot be empty")
        return v.strip().upper()

    @field_validator("site_name")
    @classmethod
    def validate_site_name(cls, v: str) -> str:
        """Validate site name"""
        if not v or v.isspace():
            raise ValueError("Site name cannot be empty")
        return v.strip()

    def is_active(self) -> bool:
        """Check if site is active"""
        return self.status == SiteStatus.ACTIVE

    def __str__(self) -> str:
        return f"NetworkSite({self.site_id}: {self.site_name})"

    def __repr__(self) -> str:
        return (
            f"NetworkSite(id={self.id}, site_id='{self.site_id}', "
            f"name='{self.site_name}', status={self.status})"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "site_id": "MSH-0112",
                "site_name": "MSH-0112-Bindura Hospital",
                "location": "Bindura Hospital",
                "latitude": -17.3011,
                "longitude": 31.3297,
                "region": "Bindura",
                "status": "active",
            }
        }


class CellTechnology(str, Enum):
    """Cell technology type"""

    LTE_4G = "4G"
    LTE_ADVANCED = "4G+"
    NR_5G = "5G"


class CellStatus(str, Enum):
    """Cell operational status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"


class NetworkCell(BaseModel):
    """
    Network Cell (individual cell within a site)

    Each site can have multiple cells (sectors).
    """

    id: Optional[int] = Field(default=None, description="Database ID")
    cell_id: str = Field(..., description="Unique cell identifier", min_length=1)
    site_id: str = Field(..., description="Parent site ID", min_length=1)
    cell_name: Optional[str] = Field(default=None, description="Human-readable cell name")
    technology: CellTechnology = Field(default=CellTechnology.LTE_4G, description="Technology")
    frequency_band: Optional[str] = Field(default=None, description="Frequency band (e.g., B3, B7)")
    pci: Optional[int] = Field(default=None, ge=0, le=503, description="Physical Cell ID")
    sector: Optional[int] = Field(default=None, ge=1, le=3, description="Sector number (1-3)")
    azimuth: Optional[int] = Field(default=None, ge=0, le=360, description="Antenna azimuth (degrees)")
    status: CellStatus = Field(default=CellStatus.ACTIVE, description="Operational status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

    @field_validator("cell_id", "site_id")
    @classmethod
    def validate_ids(cls, v: str) -> str:
        """Validate IDs"""
        if not v or v.isspace():
            raise ValueError("ID cannot be empty")
        return v.strip().upper()

    def is_active(self) -> bool:
        """Check if cell is active"""
        return self.status == CellStatus.ACTIVE

    def __str__(self) -> str:
        return f"NetworkCell({self.cell_id})"

    def __repr__(self) -> str:
        return (
            f"NetworkCell(id={self.id}, cell_id='{self.cell_id}', "
            f"site_id='{self.site_id}', status={self.status})"
        )

    class Config:
        json_schema_extra = {
            "example": {
                "cell_id": "MSH-0112_1",
                "site_id": "MSH-0112",
                "cell_name": "MSH-0112-Bindura Hospital Sector 1",
                "technology": "4G",
                "frequency_band": "B3",
                "pci": 150,
                "sector": 1,
                "azimuth": 0,
                "status": "active",
            }
        }
