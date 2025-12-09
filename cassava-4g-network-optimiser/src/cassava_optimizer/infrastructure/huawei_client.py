"""
Async client for Huawei iMaster MAE-CM API.

Provides methods for network data retrieval and MML command execution.
Uses fail-fast error handling with proper retries and rate limiting.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import structlog

from cassava_optimizer.domain.enums import CellState
from cassava_optimizer.domain.exceptions import HuaweiAPIError
from cassava_optimizer.domain.models import Cell, KPIMetric, Site

logger = structlog.get_logger(__name__)


# =============================================================================
# Huawei PM Counter ID to KPI Mapping
# =============================================================================
# These counter IDs were discovered via the PM API from the live MAE system.
# Counter ID ranges:
#   - 152672xxxx: RRC/connection related counters
#   - 152673xxxx: Traffic/throughput counters
#   - 152674xxxx: Cell-level counters

HUAWEI_COUNTER_MAPPING = {
    # RRC Connection Setup counters (Foundation tier)
    1526728514: {"kpi": "rrc_setup_attempts", "description": "RRC Setup Attempts"},
    1526728515: {"kpi": "rrc_setup_success", "description": "RRC Setup Success"},
    
    # E-RAB Setup counters (Foundation tier)
    1526728518: {"kpi": "erab_setup_attempts", "description": "E-RAB Setup Attempts"},
    1526728519: {"kpi": "erab_setup_success", "description": "E-RAB Setup Success"},
    1526728520: {"kpi": "erab_normal_release", "description": "E-RAB Normal Release"},
    
    # Traffic/Throughput counters (Revenue/Experience tier)
    1526730592: {"kpi": "pdcp_sdu_volume_dl", "description": "PDCP SDU Volume DL (MB)"},
    1526730593: {"kpi": "pdcp_sdu_volume_ul", "description": "PDCP SDU Volume UL (MB)"},
    1526730594: {"kpi": "active_ue_dl", "description": "Active UE DL Average"},
    1526730595: {"kpi": "active_ue_ul", "description": "Active UE UL Average"},
    1526730596: {"kpi": "dl_mac_throughput", "description": "DL MAC Layer Throughput (kbps)"},
    1526730597: {"kpi": "ul_mac_throughput", "description": "UL MAC Layer Throughput (kbps)"},
    
    # Additional counters
    1526737790: {"kpi": "handover_attempts", "description": "Handover Attempts"},
    1526749439: {"kpi": "cell_availability_time", "description": "Cell Availability Time"},
    1526749447: {"kpi": "dl_prb_used", "description": "DL PRB Used"},
    1526743671: {"kpi": "ul_prb_used", "description": "UL PRB Used"},
}

# Default counter IDs for PM queries - these are known to return data
DEFAULT_PM_COUNTER_IDS = [
    1526728514, 1526728515,  # RRC counters
    1526728518, 1526728519, 1526728520,  # E-RAB counters
    1526730592, 1526730593, 1526730594, 1526730595, 1526730596, 1526730597,  # Traffic
    1526737790,  # Handover
]


class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, rate: int, period: float = 1.0) -> None:
        self.rate = rate
        self.period = period
        self._tokens = rate
        self._last_refill = datetime.utcnow()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            now = datetime.utcnow()
            elapsed = (now - self._last_refill).total_seconds()
            
            # Refill tokens based on elapsed time
            self._tokens = min(
                self.rate,
                self._tokens + (elapsed / self.period) * self.rate
            )
            self._last_refill = now
            
            if self._tokens < 1:
                # Wait for token
                wait_time = (1 - self._tokens) * self.period / self.rate
                await asyncio.sleep(wait_time)
                self._tokens = 1
            
            self._tokens -= 1


class HuaweiMAEClient:
    """
    Async client for Huawei iMaster MAE Configuration Management API.
    
    Features:
    - Token-based authentication with auto-refresh
    - Rate limiting to respect API quotas
    - Automatic retry with exponential backoff
    - Connection pooling for efficiency
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = True,
        rate_limit: int = 10,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the Huawei MAE client.
        
        Args:
            host: MAE server hostname
            port: MAE API port
            username: API username
            password: API password
            use_ssl: Whether to use HTTPS
            rate_limit: Max requests per second
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        protocol = "https" if use_ssl else "http"
        self.base_url = f"{protocol}://{host}:{port}"
        self.username = username
        self.password = password
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._token: str | None = None
        self._token_expires: datetime | None = None
        self._roa_rand: str | None = None  # Huawei ROA random for some API calls
        self._rate_limiter = RateLimiter(rate_limit)
        
        # Configure HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            verify=False,  # Note: In production, use proper SSL verification
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        
        self._log = logger.bind(
            component="huawei_client",
            host=host,
        )
    
    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._client.aclose()
    
    async def __aenter__(self) -> "HuaweiMAEClient":
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.close()
    
    # =========================================================================
    # Authentication
    # =========================================================================
    
    async def authenticate(self) -> str:
        """
        Authenticate with the MAE server using OAuth and get access token.
        
        Uses Huawei iMaster MAE OAuth endpoint with PUT method.
        Auth response uses 'accessSession' token and 'X-Auth-Token' header.
        
        Returns:
            Access token
            
        Raises:
            HuaweiAPIError: If authentication fails
        """
        self._log.info("Authenticating with MAE server")
        
        try:
            # Huawei iMaster MAE OAuth endpoint (PUT method)
            response = await self._client.put(
                "/api/rest/securityManagement/v1/oauth/token",
                json={
                    "grantType": "password",
                    "userName": self.username,
                    "value": self.password,
                },
                headers={"Content-Type": "application/json"},
            )
            
            if response.status_code == 401:
                raise HuaweiAPIError.authentication_failed(self.username)
            
            if response.status_code != 200:
                raise HuaweiAPIError(
                    f"Authentication failed with status {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                    endpoint="/api/rest/securityManagement/v1/oauth/token",
                )
            
            data = response.json()
            
            # Huawei uses 'accessSession' for the token (not 'access_token')
            self._token = data.get("accessSession")
            
            if not self._token:
                raise HuaweiAPIError(
                    "No accessSession in authentication response",
                    response_body=response.text,
                )
            
            # Token expiration (Huawei provides 'expires' in seconds, default 30 min)
            expires_in = data.get("expires", 1800)
            # Use 5-minute buffer for safety
            self._token_expires = datetime.utcnow() + timedelta(seconds=expires_in - 300)
            
            # Store ROA random if available (used for some Huawei API calls)
            self._roa_rand = data.get("roaRand")
            
            self._log.info(
                "Authentication successful",
                expires_in=expires_in,
                token_prefix=self._token[:8] + "...",
            )
            return self._token
            
        except httpx.ConnectError as e:
            raise HuaweiAPIError.connection_failed(self.base_url, e)
        except httpx.TimeoutException as e:
            raise HuaweiAPIError(
                f"Authentication timed out after {self.timeout}s",
                endpoint="/api/rest/securityManagement/v1/oauth/token",
                cause=e,
            )
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid token, refreshing if needed."""
        if (
            self._token is None
            or self._token_expires is None
            or datetime.utcnow() >= self._token_expires
        ):
            await self.authenticate()
    
    # =========================================================================
    # HTTP Request Handling
    # =========================================================================
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make an authenticated API request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            HuaweiAPIError: If request fails after retries
        """
        await self._ensure_authenticated()
        await self._rate_limiter.acquire()
        
        headers = kwargs.pop("headers", {})
        # Huawei uses X-Auth-Token header (not X-Access-Token)
        headers["X-Auth-Token"] = self._token
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        
        last_error: Exception | None = None
        
        for attempt in range(self.max_retries):
            try:
                self._log.debug(
                    "API request",
                    method=method,
                    endpoint=endpoint,
                    attempt=attempt + 1,
                )
                
                response = await self._client.request(
                    method,
                    endpoint,
                    headers=headers,
                    **kwargs,
                )
                
                # Handle specific status codes
                if response.status_code == 401:
                    # Token expired, re-authenticate
                    self._token = None
                    await self._ensure_authenticated()
                    headers["X-Auth-Token"] = self._token
                    continue
                
                if response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    self._log.warning("Rate limited", retry_after=retry_after)
                    await asyncio.sleep(retry_after)
                    continue
                
                if response.status_code >= 500:
                    # Server error, retry with backoff
                    wait = 2 ** attempt
                    self._log.warning(
                        "Server error, retrying",
                        status=response.status_code,
                        wait=wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                
                if response.status_code != 200:
                    raise HuaweiAPIError(
                        f"API request failed: {response.status_code}",
                        status_code=response.status_code,
                        response_body=response.text,
                        endpoint=endpoint,
                    )
                
                return response.json()
                
            except httpx.TimeoutException as e:
                last_error = e
                self._log.warning(
                    "Request timeout",
                    endpoint=endpoint,
                    attempt=attempt + 1,
                )
                await asyncio.sleep(2 ** attempt)
            
            except httpx.ConnectError as e:
                raise HuaweiAPIError.connection_failed(self.base_url, e)
        
        raise HuaweiAPIError(
            f"Request failed after {self.max_retries} retries",
            endpoint=endpoint,
            cause=last_error,
        )
    
    # =========================================================================
    # Performance Management (PM) API
    # =========================================================================
    
    async def get_pm_data(
        self,
        site_name: str,
        counter_ids: list[int] | None = None,
        period_minutes: int = 15,
        hours_back: int = 2,
    ) -> dict[str, Any]:
        """
        Get performance measurement data from MAE PM API.
        
        This queries the Huawei iMaster MAE Performance Management API to get
        real-time and historical KPI counter values.
        
        Args:
            site_name: eNodeB site name (e.g., "MSH-0049-Kadoma Rimuka")
            counter_ids: List of counter IDs to query (uses defaults if None)
            period_minutes: Measurement period (15 or 60 minutes)
            hours_back: How many hours of data to retrieve
            
        Returns:
            Dict containing:
                - success: bool
                - counter_ids: list of counter IDs in response
                - records: list of PM records with counter values
                - task_id: PM task ID (for cleanup)
                - raw_response: full API response
                
        Raises:
            HuaweiAPIError: If PM query fails
        """
        self._log.info(
            "Querying PM data",
            site_name=site_name,
            period=period_minutes,
            hours_back=hours_back,
        )
        
        # Use default counters if none specified
        if counter_ids is None:
            counter_ids = DEFAULT_PM_COUNTER_IDS
        
        # Calculate time range (use UTC-adjusted local time for MAE)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Format: YYYY-MM-DD HH:MM:SS
        time_format = "%Y-%m-%d %H:%M:00"
        
        payload = {
            "timeFormat": "timeString",
            "startTime": start_time.strftime(time_format),
            "endTime": end_time.strftime(time_format),
            "period": period_minutes,
            "counterIds": counter_ids,
            "isQueryAllNe": 0,
            "neTypeName": "eNodeB",
            "neNames": [site_name],
        }
        
        self._log.debug("PM API request", payload=payload)
        
        await self._ensure_authenticated()
        await self._rate_limiter.acquire()
        
        try:
            response = await self._client.post(
                "/api/rest/performanceManagement/v1/measurementResults",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Auth-Token": self._token,
                },
            )
            
            if response.status_code not in (200, 202):
                raise HuaweiAPIError(
                    f"PM query failed: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                    endpoint="/api/rest/performanceManagement/v1/measurementResults",
                )
            
            data = response.json()
            task_id = data.get("taskId")
            ret_code = data.get("retCode", "")
            ret_message = data.get("retMessage", "")
            
            # Handle async response (202)
            if response.status_code == 202 and task_id:
                # Poll for results
                data = await self._poll_pm_results(task_id)
            
            # Check for "no data" response
            if ret_code == "90042":
                self._log.warning(
                    "PM query returned no data - counter subscriptions may not be configured",
                    site_name=site_name,
                    ret_code=ret_code,
                    ret_message=ret_message,
                )
                return {
                    "success": False,
                    "counter_ids": [],
                    "records": [],
                    "task_id": task_id,
                    "error": "No PM data available - counter subscriptions not configured",
                    "raw_response": data,
                }
            
            # Parse successful response
            records = self._parse_pm_response(data)
            
            self._log.info(
                "PM data retrieved",
                site_name=site_name,
                record_count=len(records),
                counter_count=len(data.get("counterIds", [])),
            )
            
            return {
                "success": ret_code == "90000",
                "counter_ids": data.get("counterIds", []),
                "records": records,
                "task_id": task_id,
                "period": data.get("period", period_minutes),
                "raw_response": data,
            }
            
        except httpx.TimeoutException as e:
            raise HuaweiAPIError(
                f"PM query timed out after {self.timeout}s",
                endpoint="/api/rest/performanceManagement/v1/measurementResults",
                cause=e,
            )
        finally:
            # Cleanup task if we got one
            task_id = data.get("taskId") if "data" in dir() else None
            if task_id:
                await self._delete_pm_task(task_id)
    
    async def _poll_pm_results(
        self,
        task_id: str,
        max_attempts: int = 5,
        poll_interval: float = 2.0,
    ) -> dict[str, Any]:
        """Poll for PM results when task is async."""
        for attempt in range(max_attempts):
            await asyncio.sleep(poll_interval)
            
            response = await self._client.get(
                f"/api/rest/performanceManagement/v1/measurementResults/{task_id}",
                headers={
                    "Accept": "application/json",
                    "X-Auth-Token": self._token,
                },
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 202:
                self._log.debug("PM results still collecting", attempt=attempt + 1)
                continue
            else:
                raise HuaweiAPIError(
                    f"PM poll failed: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                )
        
        raise HuaweiAPIError(f"PM results not ready after {max_attempts} attempts")
    
    async def _delete_pm_task(self, task_id: str) -> None:
        """Delete a PM query task to free resources."""
        try:
            await self._client.delete(
                f"/api/rest/performanceManagement/v1/measurementResults/{task_id}",
                headers={
                    "Accept": "application/json",
                    "X-Auth-Token": self._token,
                },
            )
            self._log.debug("PM task deleted", task_id=task_id)
        except Exception as e:
            self._log.warning("Failed to delete PM task", task_id=task_id, error=str(e))
    
    def _parse_pm_response(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse PM API response into structured records."""
        records = []
        counter_ids = data.get("counterIds", [])
        results = data.get("result", [])
        
        for result in results:
            counter_values = result.get("counterValues", [])
            
            # Map counter IDs to values
            mapped_values = {}
            for i, counter_id in enumerate(counter_ids):
                if i < len(counter_values):
                    value = counter_values[i]
                    # Handle NIL values
                    if value != "NIL":
                        try:
                            mapped_values[counter_id] = float(value)
                        except (ValueError, TypeError):
                            mapped_values[counter_id] = 0.0
                    else:
                        mapped_values[counter_id] = None
            
            records.append({
                "ne_name": result.get("neName", ""),
                "ne_fdn": result.get("neFdn", ""),
                "object_name": result.get("objectName", ""),
                "start_time": result.get("startTime", ""),
                "counter_values": mapped_values,
            })
        
        return records
    
    def convert_pm_to_kpis(
        self,
        pm_data: dict[str, Any],
        site_id: str,
    ) -> dict[str, float]:
        """
        Convert PM counter data to KPI values.
        
        Aggregates counter values across cells and calculates derived KPIs.
        
        Note: Counter ID to KPI mapping was discovered empirically.
        The counter IDs 152672xxxx are RRC/E-RAB related and 152673xxxx are traffic related.
        
        Args:
            pm_data: PM data from get_pm_data()
            site_id: Site identifier for KPI metrics
            
        Returns:
            Dict of KPI name -> value
        """
        if not pm_data.get("success") or not pm_data.get("records"):
            return {}
        
        # Aggregate counters across all records (cells/time periods)
        # Track both values and whether we saw any data
        counter_totals: dict[int, list[float]] = {}
        has_any_counter_data = False
        
        for record in pm_data["records"]:
            for counter_id, value in record.get("counter_values", {}).items():
                if value is not None:
                    has_any_counter_data = True
                    if value >= 0:  # Include zero values for proper averaging
                        if counter_id not in counter_totals:
                            counter_totals[counter_id] = []
                        counter_totals[counter_id].append(value)
        
        # If no counter data at all, return empty
        if not has_any_counter_data:
            return {}
        
        # Calculate KPIs from counter aggregates
        kpis = {}
        
        # RRC Setup Success Rate
        # Counter 1526728514 = RRC attempts, 1526728515 = RRC success
        # Note: In some cases, success count may be reported without attempts.
        # If we have success but no attempts, use success count as attempts (100% rate)
        rrc_attempts_values = counter_totals.get(1526728514, [])
        rrc_success_values = counter_totals.get(1526728515, [])
        
        if rrc_success_values:
            total_success = sum(rrc_success_values)
            # If attempts not tracked, assume all were successful
            total_attempts = sum(rrc_attempts_values) if rrc_attempts_values else total_success
            
            if total_attempts > 0:
                kpis["rrc_setup_success_rate"] = min((total_success / total_attempts) * 100, 100.0)
        
        # E-RAB Setup Success Rate
        # Counter 1526728518 = attempts, 1526728519 = success
        # Same handling as RRC - use success as baseline if attempts not available
        erab_attempts_values = counter_totals.get(1526728518, [])
        erab_success_values = counter_totals.get(1526728519, [])
        
        if erab_success_values:
            total_success = sum(erab_success_values)
            # If attempts not tracked, assume all were successful
            total_attempts = sum(erab_attempts_values) if erab_attempts_values else total_success
            
            if total_attempts > 0:
                kpis["erab_setup_success_rate"] = min((total_success / total_attempts) * 100, 100.0)
        
        # Throughput (average values, convert kbps to Mbps)
        # Counter 1526730596 = DL throughput (kbps), 1526730597 = UL throughput (kbps)
        dl_throughput_values = counter_totals.get(1526730596, [])
        ul_throughput_values = counter_totals.get(1526730597, [])
        
        # Always report throughput if we have data (even if 0)
        if dl_throughput_values:
            # Filter out zeros for average (low traffic periods)
            non_zero_dl = [v for v in dl_throughput_values if v > 0]
            if non_zero_dl:
                avg_dl = sum(non_zero_dl) / len(non_zero_dl)
            else:
                avg_dl = 0  # All zeros = no traffic
            kpis["dl_throughput"] = avg_dl / 1000  # kbps to Mbps
            
        if ul_throughput_values:
            non_zero_ul = [v for v in ul_throughput_values if v > 0]
            if non_zero_ul:
                avg_ul = sum(non_zero_ul) / len(non_zero_ul)
            else:
                avg_ul = 0
            kpis["ul_throughput"] = avg_ul / 1000  # kbps to Mbps
        
        # Active UE Count (average across periods)
        # Counter 1526730594 = Active UE DL, 1526730595 = Active UE UL
        active_dl = counter_totals.get(1526730594, [])
        active_ul = counter_totals.get(1526730595, [])
        
        if active_dl:
            non_zero_active = [v for v in active_dl if v > 0]
            kpis["active_ue_dl"] = sum(non_zero_active) / len(non_zero_active) if non_zero_active else 0
        if active_ul:
            non_zero_active = [v for v in active_ul if v > 0]
            kpis["active_ue_ul"] = sum(non_zero_active) / len(non_zero_active) if non_zero_active else 0
        
        # Total PDCP Volume (sum, convert to MB if needed)
        # Counter 1526730592 = PDCP DL, 1526730593 = PDCP UL
        # Note: Unit depends on MAE configuration - assume already in MB
        pdcp_dl = counter_totals.get(1526730592, [])
        pdcp_ul = counter_totals.get(1526730593, [])
        
        if pdcp_dl:
            kpis["pdcp_dl_volume_mb"] = sum(pdcp_dl)
        if pdcp_ul:
            kpis["pdcp_ul_volume_mb"] = sum(pdcp_ul)
        
        # Handover attempts (sum)
        # Counter 1526737790
        handover = counter_totals.get(1526737790, [])
        if handover:
            kpis["handover_attempts"] = sum(handover)
        
        # Cell Availability (if available)
        # Counter 1526749439 - availability time
        availability = counter_totals.get(1526749439, [])
        if availability:
            # If this is percentage directly, average it
            kpis["cell_availability"] = sum(availability) / len(availability)
        
        self._log.debug("PM to KPI conversion", kpis=kpis)
        return kpis

    # =========================================================================
    # Alarm API (Network Health)
    # =========================================================================
    
    async def get_alarms(
        self,
        data_type: str = "CURRENT",
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Get alarms from MAE Fault Management API.
        
        This provides network health status and can be used when PM data
        is not available.
        
        Args:
            data_type: CURRENT, HISTORY, or LOG
            limit: Maximum alarms to return
            
        Returns:
            Dict containing:
                - success: bool
                - alarms: list of alarm records
                - summary: severity breakdown
        """
        self._log.info("Querying alarms", data_type=data_type, limit=limit)
        
        await self._ensure_authenticated()
        await self._rate_limiter.acquire()
        
        try:
            response = await self._client.get(
                "/api/rest/faultSupervisonManagement/v1/alarms",
                params={
                    "dataType": data_type,
                    "limit": limit,
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Accept-Language": "en-US",
                    "X-Auth-Token": self._token,
                },
            )
            
            if response.status_code != 200:
                raise HuaweiAPIError(
                    f"Alarm query failed: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text,
                    endpoint="/api/rest/faultSupervisonManagement/v1/alarms",
                )
            
            data = response.json()
            alarms = data.get("alarmInformationList", [])
            
            # Summarize by severity
            severity_map = {
                "1": "critical", "2": "major", "3": "minor",
                "4": "warning", "5": "indeterminate", "6": "cleared"
            }
            summary = {}
            for alarm in alarms:
                sev = str(alarm.get("perceivedSeverity", "?"))
                sev_name = severity_map.get(sev, "unknown")
                summary[sev_name] = summary.get(sev_name, 0) + 1
            
            self._log.info("Alarms retrieved", count=len(alarms), summary=summary)
            
            return {
                "success": True,
                "alarms": alarms,
                "summary": summary,
                "total": len(alarms),
                "raw_response": data,
            }
            
        except httpx.TimeoutException as e:
            raise HuaweiAPIError(
                f"Alarm query timed out",
                endpoint="/api/rest/faultSupervisonManagement/v1/alarms",
                cause=e,
            )

    # =========================================================================
    # Network Data Retrieval
    # =========================================================================
    
    async def get_sites(self) -> list[Site]:
        """
        Get all eNodeB sites from MAE.
        
        Returns:
            List of Site domain objects
        """
        self._log.info("Fetching sites from MAE")
        
        response = await self._request(
            "GET",
            "/restconf/v1/data/network-inventory:network-inventory/nodes",
        )
        
        nodes = response.get("nodes", {}).get("node", [])
        sites = []
        
        for node in nodes:
            if node.get("node-type") == "eNodeB":
                site = self._parse_site(node)
                if site:
                    sites.append(site)
        
        self._log.info("Sites fetched", count=len(sites))
        return sites
    
    async def get_site_details(self, site_id: str) -> Site:
        """
        Get detailed site information including cells.
        
        Args:
            site_id: Site identifier
            
        Returns:
            Site domain object with cells
        """
        self._log.info("Fetching site details", site_id=site_id)
        
        response = await self._request(
            "GET",
            f"/restconf/v1/data/network-inventory:network-inventory/nodes/node={site_id}",
        )
        
        node = response.get("node", [{}])[0]
        site = self._parse_site(node)
        
        if not site:
            raise HuaweiAPIError(
                f"Site {site_id} not found",
                endpoint=f"/nodes/node={site_id}",
            )
        
        # Get cells for this site
        cells = await self.get_cells(site_id)
        
        return Site(
            **{**site.model_dump(), "cells": tuple(cells)}
        )
    
    async def get_cells(self, site_id: str) -> list[Cell]:
        """
        Get all cells for a site.
        
        Args:
            site_id: Site identifier
            
        Returns:
            List of Cell domain objects
        """
        self._log.info("Fetching cells", site_id=site_id)
        
        response = await self._request(
            "GET",
            f"/restconf/v1/data/network-inventory:network-inventory/nodes/node={site_id}/cells",
        )
        
        cells_data = response.get("cells", {}).get("cell", [])
        cells = []
        
        for cell_data in cells_data:
            cell = self._parse_cell(cell_data, site_id)
            if cell:
                cells.append(cell)
        
        self._log.info("Cells fetched", site_id=site_id, count=len(cells))
        return cells
    
    async def get_kpi_data(
        self,
        site_id: str,
        kpi_names: list[str] | None = None,
    ) -> list[KPIMetric]:
        """
        Get real-time KPI data for a site.
        
        Args:
            site_id: Site identifier
            kpi_names: Optional list of specific KPIs to retrieve
            
        Returns:
            List of KPI metrics
        """
        self._log.info("Fetching KPI data", site_id=site_id, kpis=kpi_names)
        
        # Build KPI query parameters
        params = {"node-id": site_id}
        if kpi_names:
            params["kpi-names"] = ",".join(kpi_names)
        
        response = await self._request(
            "GET",
            "/restconf/v1/data/performance-data:performance-data/kpis",
            params=params,
        )
        
        kpis_data = response.get("kpis", {}).get("kpi", [])
        metrics = []
        
        for kpi_data in kpis_data:
            metric = self._parse_kpi(kpi_data, site_id)
            if metric:
                metrics.append(metric)
        
        self._log.info("KPIs fetched", site_id=site_id, count=len(metrics))
        return metrics
    
    # =========================================================================
    # MML Command Execution
    # =========================================================================
    
    async def execute_mml_command(
        self,
        site_id: str,
        command: str,
    ) -> dict[str, Any]:
        """
        Execute an MML command on an eNodeB.
        
        Uses Huawei iMaster MAE MML Management API.
        
        IMPORTANT:
        - QUERY commands (LST) work site-wide and return data for all cells
        - MODIFY commands (MOD) must include LOCALCELLID and are cell-specific
        
        Args:
            site_id: Target site/eNodeB name (e.g., "MSH-0112-Bindura Hospital")
            command: MML command string
                Query example: "LST UECOOPERATIONPARA:;"
                Modify example: "MOD PDSCHCFG:LOCALCELLID=1,REFERENCESIGNALPWR=-180;"
            
        Returns:
            Command execution result with output
            
        Raises:
            HuaweiAPIError: If command execution fails
        """
        self._log.info(
            "Executing MML command",
            site_id=site_id,
            command=command[:50] + "...",
        )
        
        # Huawei MML Management API endpoint
        response = await self._request(
            "POST",
            "/api/rest/mmlManagement/v1/command",
            json={
                "command": command,
                "neNames": [site_id],  # Huawei expects 'neNames' (NE = Network Element)
            },
        )
        
        # Parse response - Huawei returns different format
        success = response.get("errCode") == "0" or response.get("result") == "success"
        result = {
            "success": success,
            "output": response.get("commandResponse", response.get("output", "")),
            "error_code": response.get("errCode", "0"),
            "error_message": response.get("errMsg", ""),
            "raw_response": response,
        }
        
        self._log.info(
            "MML command completed",
            site_id=site_id,
            success=result["success"],
        )
        
        return result
    
    # =========================================================================
    # Data Parsers
    # =========================================================================
    
    def _parse_site(self, node: dict[str, Any]) -> Site | None:
        """Parse site data from API response."""
        try:
            return Site(
                site_id=node.get("node-id", ""),
                site_name=node.get("node-name", ""),
                enodeb_id=int(node.get("enodeb-id", 0)),
                latitude=float(node.get("latitude", 0)),
                longitude=float(node.get("longitude", 0)),
                region=node.get("region", ""),
                cluster=node.get("cluster", ""),
                cells=(),
            )
        except (ValueError, KeyError) as e:
            self._log.warning("Failed to parse site", error=str(e), node_id=node.get("node-id"))
            return None
    
    def _parse_cell(self, cell_data: dict[str, Any], site_id: str) -> Cell | None:
        """Parse cell data from API response."""
        try:
            state_str = cell_data.get("state", "unknown").lower()
            state = CellState(state_str) if state_str in CellState.__members__ else CellState.UNKNOWN
            
            return Cell(
                cell_id=cell_data.get("cell-id", ""),
                local_cell_id=int(cell_data.get("local-cell-id", 0)),
                cell_name=cell_data.get("cell-name", ""),
                site_id=site_id,
                pci=int(cell_data.get("pci", 0)),
                tac=int(cell_data.get("tac", 0)),
                earfcn=int(cell_data.get("earfcn", 0)),
                bandwidth=int(cell_data.get("bandwidth", 10)),
                azimuth=float(cell_data.get("azimuth", 0)),
                electrical_tilt=float(cell_data.get("electrical-tilt", 0)),
                mechanical_tilt=float(cell_data.get("mechanical-tilt", 0)),
                tx_power=float(cell_data.get("tx-power", 40)),
                state=state,
            )
        except (ValueError, KeyError) as e:
            self._log.warning(
                "Failed to parse cell",
                error=str(e),
                cell_id=cell_data.get("cell-id"),
            )
            return None
    
    def _parse_kpi(self, kpi_data: dict[str, Any], site_id: str) -> KPIMetric | None:
        """Parse KPI data from API response."""
        # Note: This is a simplified parser. The actual parsing would depend
        # on the KPI definitions from kpi_definitions.py
        try:
            from cassava_optimizer.domain.kpi_definitions import get_kpi_definition
            
            kpi_name = kpi_data.get("kpi-name", "")
            kpi_def = get_kpi_definition(kpi_name)
            
            if kpi_def:
                return kpi_def.create_metric(
                    value=float(kpi_data.get("value", 0)),
                    site_id=site_id,
                    cell_id=kpi_data.get("cell-id", ""),
                )
            
            return None
        except (ValueError, KeyError) as e:
            self._log.warning(
                "Failed to parse KPI",
                error=str(e),
                kpi_name=kpi_data.get("kpi-name"),
            )
            return None
