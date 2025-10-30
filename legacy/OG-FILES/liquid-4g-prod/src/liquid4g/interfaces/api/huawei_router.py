"""
Huawei API endpoints for network management operations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status

from liquid4g.infrastructure.api.huawei_client import HuaweiClient
from liquid4g.core.logging import get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/huawei", tags=["huawei"])

# Global Huawei client instance
_huawei_client = None

def get_huawei_client() -> HuaweiClient:
    """Get or create Huawei client instance"""
    global _huawei_client
    if _huawei_client is None:
        _huawei_client = HuaweiClient()
    return _huawei_client

@router.get("/health")
async def huawei_health_check() -> Dict[str, Any]:
    """
    Check Huawei API health and connectivity
    """
    try:
        client = get_huawei_client()
        
        # Perform health check using the client
        health_result = await client.health_check()
        
        return {
            "status": "healthy" if health_result.get("authenticated", False) else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "details": health_result
        }
        
    except Exception as e:
        logger.error(f"Huawei health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Huawei API health check failed: {str(e)}"
        )

@router.get("/status")
async def huawei_connection_status() -> Dict[str, Any]:
    """
    Get detailed Huawei API connection status
    """
    try:
        client = get_huawei_client()
        
        # Get configuration status
        config_status = await client.get_configuration_status()
        
        return {
            "connected": config_status.get("is_connected", False),
            "authenticated": config_status.get("is_authenticated", False),
            "network_elements": config_status.get("network_elements_count", 0),
            "parameters": config_status.get("parameter_configs_count", 0),
            "last_check": config_status.get("last_check"),
            "api_health": config_status.get("api_health", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Failed to get Huawei connection status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Huawei connection status: {str(e)}"
        )

@router.get("/network-elements")
async def get_network_elements() -> Dict[str, Any]:
    """
    Get list of available Huawei network elements
    """
    try:
        client = get_huawei_client()
        
        # Get network elements from client
        elements = await client.get_network_elements()
        
        return {
            "count": len(elements),
            "elements": [
                {
                    "name": element.name,
                    "site_id": element.site_id,
                    "cell_ids": element.cell_ids,
                    "location": element.location
                }
                for element in elements
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get network elements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get network elements: {str(e)}"
        )

@router.post("/execute")
async def execute_mml_command(
    command: str,
    network_elements: List[str],
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute MML command on specified network elements
    """
    try:
        client = get_huawei_client()
        
        # Execute the command
        result = await client.execute_mml_command(command, network_elements)
        
        return {
            "command": command,
            "network_elements": network_elements,
            "description": description,
            "execution_time": datetime.now().isoformat(),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to execute MML command: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute MML command: {str(e)}"
        )