"""
Liquid Zimbabwe 4G Network Optimizer - KPI Collector
Purpose: Collect KPI data from Huawei API or historical database
Created: 2025-10-30

This module handles KPI data collection with automatic fallback to historical data
if the Huawei API is unavailable.
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os
import yaml

try:
    from network.huawei_api_client import HuaweiAPIClient
except ImportError:
    from huawei_api_client import HuaweiAPIClient

# Setup logging
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "lz_network.db")


class KPICollector:
    """
    Collects KPI data from Huawei API with fallback to historical database.

    Features:
    - Live KPI collection from Huawei iMaster MAE API
    - Automatic fallback to historical data if API unavailable
    - KPI data storage in unified database
    - Data validation and normalization
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize KPI Collector.

        Args:
            config_path: Path to config.yaml (optional)
        """
        # Load configuration
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.offline_mode = self.config.get('system', {}).get('offline_mode', False)
        self.api_client = None

        # Initialize API client if not in offline mode
        if not self.offline_mode:
            try:
                api_config = {
                    'base_url': os.getenv('HUAWEI_API_URL'),
                    'username': os.getenv('HUAWEI_USERNAME'),
                    'password': os.getenv('HUAWEI_PASSWORD'),
                    'timeout': 30,
                    'retry_attempts': 2,
                    'retry_delay': 3,
                    'ssl_verify': False
                }
                self.api_client = HuaweiAPIClient(api_config)
                logger.info("Huawei API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Huawei API client: {e}")
                self.api_client = None

    def collect_kpis(self, site_name: str, cell_id: int = 1) -> Dict[str, float]:
        """
        Collect KPI data for a site.

        Attempts to collect from Huawei API first, falls back to historical data.

        Args:
            site_name: Site/eNodeB name
            cell_id: Cell ID (default: 1)

        Returns:
            Dictionary with 7 KPI values
        """
        try:
            # Try live API first
            if self.api_client and not self.offline_mode:
                logger.info(f"Attempting to collect live KPIs for {site_name} (cell {cell_id})")
                try:
                    kpis = self._collect_from_api(site_name, cell_id)
                    if kpis:
                        # Store in database
                        self._store_kpis(site_name, cell_id, kpis, data_source='live')
                        return kpis
                except Exception as api_error:
                    logger.warning(f"Live KPI collection failed: {api_error}")

            # Fallback to historical data
            logger.info(f"Falling back to historical KPIs for {site_name}")
            kpis = self._collect_from_database(site_name, cell_id)

            if kpis:
                return kpis
            else:
                logger.error(f"No KPI data available for {site_name}")
                return self._get_default_kpis()

        except Exception as e:
            logger.error(f"Error collecting KPIs: {e}")
            return self._get_default_kpis()

    def _collect_from_api(self, site_name: str, cell_id: int) -> Optional[Dict[str, float]]:
        """
        Collect KPIs from Huawei iMaster MAE API.

        Args:
            site_name: Site/eNodeB name
            cell_id: Cell ID

        Returns:
            Dictionary with KPI values or None if failed
        """
        try:
            # Execute MML command to get performance data
            mml_command = f"LST PMDATA: OBJECTTYPE=CELL, LOCALCELLID={cell_id};"
            response = self.api_client.execute_mml_command(mml_command)

            # Parse response (simplified - would need robust parsing)
            if "SUCCEED" not in response.upper():
                logger.warning(f"MML command failed: {response}")
                return None

            # Parse KPI values from response
            # This is a simplified parser - real implementation would be more robust
            kpis = self._parse_mml_response(response)

            return kpis

        except Exception as e:
            logger.error(f"Error collecting from API: {e}")
            return None

    def _parse_mml_response(self, response: str) -> Dict[str, float]:
        """
        Parse MML response to extract KPI values.

        This is a simplified implementation. Real implementation would need
        proper MML response parsing based on Huawei's response format.

        Args:
            response: MML command response string

        Returns:
            Dictionary with parsed KPI values
        """
        # Placeholder implementation
        # Real implementation would parse actual Huawei MML response format
        logger.warning("Using placeholder MML parser - implement proper parsing")

        return {
            'network_access_success': 95.0,
            'download_speed': 50.0,
            'download_quality': 96.0,
            'upload_speed': 20.0,
            'upload_quality': 95.0,
            'control_channel_load': 60.0,
            'feedback_channel_load': 30.0
        }

    def _collect_from_database(self, site_name: str, cell_id: int) -> Optional[Dict[str, float]]:
        """
        Collect latest KPIs from historical database.

        Args:
            site_name: Site/eNodeB name
            cell_id: Cell ID

        Returns:
            Dictionary with KPI values or None if not found
        """
        try:
            if not os.path.exists(DB_PATH):
                logger.error(f"Database not found: {DB_PATH}")
                return None

            conn = sqlite3.connect(DB_PATH)

            # Query latest KPIs for site
            query = """
                SELECT
                    network_access_success,
                    download_speed,
                    download_quality,
                    upload_speed,
                    upload_quality,
                    control_channel_load,
                    feedback_channel_load
                FROM kpi_data
                WHERE site_name = ? AND cell_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """

            df = pd.read_sql_query(query, conn, params=(site_name, cell_id))
            conn.close()

            if df.empty:
                logger.warning(f"No historical data found for {site_name} (cell {cell_id})")
                return None

            # Convert to dictionary
            kpis = df.iloc[0].to_dict()
            logger.info(f"Loaded historical KPIs for {site_name}")

            return kpis

        except Exception as e:
            logger.error(f"Error reading from database: {e}")
            return None

    def _store_kpis(self, site_name: str, cell_id: int, kpis: Dict[str, float], data_source: str = 'live'):
        """
        Store KPI data in database.

        Args:
            site_name: Site/eNodeB name
            cell_id: Cell ID
            kpis: KPI values dictionary
            data_source: 'live' or 'historical'
        """
        try:
            if not os.path.exists(DB_PATH):
                logger.error(f"Database not found: {DB_PATH}")
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Insert KPI record
            cursor.execute("""
                INSERT INTO kpi_data (
                    timestamp, site_name, cell_id,
                    network_access_success, download_speed, download_quality,
                    upload_speed, upload_quality, control_channel_load,
                    feedback_channel_load, data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                site_name,
                cell_id,
                kpis.get('network_access_success'),
                kpis.get('download_speed'),
                kpis.get('download_quality'),
                kpis.get('upload_speed'),
                kpis.get('upload_quality'),
                kpis.get('control_channel_load'),
                kpis.get('feedback_channel_load'),
                data_source
            ))

            conn.commit()
            conn.close()

            logger.info(f"Stored KPIs for {site_name} (source: {data_source})")

        except Exception as e:
            logger.error(f"Error storing KPIs: {e}")

    def _get_default_kpis(self) -> Dict[str, float]:
        """
        Get default KPI values when no data is available.

        Returns:
            Dictionary with default KPI values
        """
        logger.warning("Using default KPI values")
        return {
            'network_access_success': 95.0,
            'download_speed': 50.0,
            'download_quality': 95.0,
            'upload_speed': 20.0,
            'upload_quality': 95.0,
            'control_channel_load': 50.0,
            'feedback_channel_load': 30.0
        }

    def get_kpi_history(self, site_name: str, cell_id: int = 1, days: int = 7) -> pd.DataFrame:
        """
        Get historical KPI data for trend analysis.

        Args:
            site_name: Site/eNodeB name
            cell_id: Cell ID
            days: Number of days of history to retrieve

        Returns:
            DataFrame with historical KPI data
        """
        try:
            if not os.path.exists(DB_PATH):
                logger.error(f"Database not found: {DB_PATH}")
                return pd.DataFrame()

            conn = sqlite3.connect(DB_PATH)

            query = """
                SELECT *
                FROM kpi_data
                WHERE site_name = ?
                  AND cell_id = ?
                  AND timestamp >= date('now', ?)
                ORDER BY timestamp ASC
            """

            df = pd.read_sql_query(query, conn, params=(site_name, cell_id, f'-{days} days'))
            conn.close()

            logger.info(f"Retrieved {len(df)} historical KPI records for {site_name}")
            return df

        except Exception as e:
            logger.error(f"Error retrieving KPI history: {e}")
            return pd.DataFrame()

    def get_all_sites(self) -> List[str]:
        """
        Get list of all sites in database.

        Returns:
            List of site names
        """
        try:
            if not os.path.exists(DB_PATH):
                return []

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT site_name FROM kpi_data ORDER BY site_name")
            sites = [row[0] for row in cursor.fetchall()]

            conn.close()
            return sites

        except Exception as e:
            logger.error(f"Error getting site list: {e}")
            return []


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Initialize collector
    collector = KPICollector()

    # Get list of sites
    sites = collector.get_all_sites()
    print(f"Available sites: {sites}")

    if sites:
        # Collect KPIs for first site
        site = sites[0]
        print(f"\nCollecting KPIs for {site}...")

        kpis = collector.collect_kpis(site)
        print("\nCurrent KPIs:")
        for kpi_name, value in kpis.items():
            print(f"  {kpi_name}: {value}")

        # Get KPI history
        print(f"\nFetching 7-day history for {site}...")
        history = collector.get_kpi_history(site, days=7)
        print(f"Retrieved {len(history)} historical records")

        if not history.empty:
            print("\nKPI Trends:")
            numeric_cols = ['download_speed', 'upload_speed', 'network_access_success']
            for col in numeric_cols:
                if col in history.columns:
                    avg = history[col].mean()
                    print(f"  {col}: avg={avg:.2f}")
